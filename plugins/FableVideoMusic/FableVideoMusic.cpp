#include "FableVideoMusic.h"
#include <cmath>
using namespace ffglex;

enum ParamType : FFUInt32
{
	PT_LEVEL,
	PT_PATTERN,
	PT_CHUNK,
	PT_CYCLE,
	PT_SOLID
};

static CFFGLPluginInfo PluginInfo(
	PluginFactory< FableVideoMusic >,                                              // Create method
	"FAVM",                                                                        // Plugin unique ID of maximum length 4.
	"Fable Video Music",                                                           // Plugin name
	2,                                                                             // API major version number
	1,                                                                             // API minor version number
	1,                                                                             // Plugin major version number
	0,                                                                             // Plugin minor version number
	FF_SOURCE,                                                                     // Plugin type
	"1977 - Atari Video Music: the first consumer music visualizer, diamonds on your hi-fi.", // Plugin description
	"Fable / Res_Fable rig"                                                        // About
);

static const char _vertexShaderCode[] = R"(#version 410 core
layout( location = 0 ) in vec4 vPosition;
layout( location = 1 ) in vec2 vUV;

out vec2 uv;

void main()
{
	gl_Position = vPosition;
	uv = vUV;
}
)";

static const char _fragmentShaderCode[] = R"(#version 410 core
uniform float Time;
uniform float Level;
uniform float Pattern;
uniform float Chunk;
uniform float Cycle;
uniform float Solid;

in vec2 uv;

out vec4 fragColor;

//Fixed 70s palette: orange, magenta, cyan, green, yellow, red, blue, white.
const vec3 PALETTE[ 8 ] = vec3[ 8 ](
	vec3( 1.0, 0.5, 0.0 ),
	vec3( 1.0, 0.0, 1.0 ),
	vec3( 0.0, 1.0, 1.0 ),
	vec3( 0.0, 1.0, 0.0 ),
	vec3( 1.0, 1.0, 0.0 ),
	vec3( 1.0, 0.0, 0.0 ),
	vec3( 0.0, 0.0, 1.0 ),
	vec3( 1.0, 1.0, 1.0 ) );

vec3 paletteColor( float idx )
{
	int i = int( mod( idx, 8.0 ) );
	return PALETTE[ i ];
}

void main()
{
	//Chunky raster grid: quantize coordinates to 8-40 cells.
	float cells = mix( 8.0, 40.0, clamp( Chunk, 0.0, 1.0 ) );
	vec2 qp = ( floor( uv * cells ) + 0.5 ) / cells;

	//Stepped palette rotation - hard color jumps, like the original raster hardware.
	float cycleStep = floor( Time * Cycle * 8.0 );
	float level = clamp( Level, 0.0, 1.0 );
	int mode = int( min( Pattern, 0.999 ) * 4.0 );
	float litFrac = mix( 0.30, 1.0, clamp( Solid, 0.0, 1.0 ) );

	vec3 col = vec3( 0.0 );

	if( mode == 0 )
	{
		//Nested diamonds growing from center with Level.
		float d = abs( qp.x - 0.5 ) + abs( qp.y - 0.5 );
		float span = 0.06 + level * 0.94;
		float ringW = span / 5.0;
		if( d < span )
		{
			float ringF = d / ringW;
			float ring  = floor( ringF );
			float local = fract( ringF );
			if( local > 1.0 - litFrac )
				col = paletteColor( ring + cycleStep );
		}
	}
	else if( mode == 1 )
	{
		//Vertical bars rising from the bottom, heights waving across the row.
		float barCount = 16.0;
		float bar = floor( qp.x * barCount );
		float h = level * ( 0.35 + 0.65 * ( 0.5 + 0.5 * sin( bar * 0.7 + Time * 1.8 ) ) );
		if( qp.y < h && qp.y > h * ( 1.0 - litFrac ) )
			col = paletteColor( bar + cycleStep );
	}
	else if( mode == 2 )
	{
		//Concentric rectangles pulsing from center.
		float d = max( abs( qp.x - 0.5 ), abs( qp.y - 0.5 ) ) * 2.0;
		float span = 0.06 + level * 0.94;
		float ringW = span / 5.0;
		if( d < span )
		{
			float ringF = d / ringW;
			float ring  = floor( ringF );
			float local = fract( ringF );
			if( local > 1.0 - litFrac )
				col = paletteColor( ring + cycleStep + 3.0 );
		}
	}
	else
	{
		//Split mirror diamonds: four mirrored quadrant tiles.
		vec2 f = qp * 2.0;
		vec2 cell = floor( f );
		vec2 loc = fract( f );
		loc = mix( loc, 1.0 - loc, mod( cell, vec2( 2.0 ) ) );
		float d = abs( loc.x - 0.5 ) + abs( loc.y - 0.5 );
		float span = 0.06 + level * 0.94;
		float ringW = span / 4.0;
		if( d < span )
		{
			float ringF = d / ringW;
			float ring  = floor( ringF );
			float local = fract( ringF );
			if( local > 1.0 - litFrac )
				col = paletteColor( ring + cycleStep + cell.x + cell.y * 2.0 );
		}
	}

	//Opaque black background, premultiplied output.
	fragColor = vec4( col, 1.0 );
}
)";

FableVideoMusic::FableVideoMusic() :
	level( 0.5f ), pattern( 0.0f ), chunk( 0.4f ), cycle( 0.3f ), solid( 0.5f ),
	lastHostTime( 0.0 ), localTime( 0.0 )
{
	//This is a source plugin: no input textures.
	SetMinInputs( 0 );
	SetMaxInputs( 0 );

	//The SDK does not initialise hostTime; zero it so our clock fallback is deterministic.
	hostTime = 0.0;

	SetParamInfo( PT_LEVEL, "Level", FF_TYPE_STANDARD, 0.5f );
	SetParamInfo( PT_PATTERN, "Pattern", FF_TYPE_STANDARD, 0.0f );
	SetParamInfo( PT_CHUNK, "Chunk", FF_TYPE_STANDARD, 0.4f );
	SetParamInfo( PT_CYCLE, "Cycle", FF_TYPE_STANDARD, 0.3f );
	SetParamInfo( PT_SOLID, "Solid", FF_TYPE_STANDARD, 0.5f );

	FFGLLog::LogToHost( "Created Fable Video Music source" );
}
FableVideoMusic::~FableVideoMusic()
{
}

FFResult FableVideoMusic::InitGL( const FFGLViewportStruct* vp )
{
	if( !shader.Compile( _vertexShaderCode, _fragmentShaderCode ) )
	{
		DeInitGL();
		return FF_FAIL;
	}
	if( !quad.Initialise() )
	{
		DeInitGL();
		return FF_FAIL;
	}

	//Use base-class init as success result so that it retains the viewport.
	return CFFGLPlugin::InitGL( vp );
}
FFResult FableVideoMusic::ProcessOpenGL( ProcessOpenGLStruct* pGL )
{
	//Advance the plugin clock: prefer host-provided time (SetTime), fall back to a 60 fps step.
	double delta = hostTime - lastHostTime;
	if( delta <= 0.0 || delta > 0.5 )
		delta = 1.0 / 60.0;
	localTime += delta;
	lastHostTime = hostTime;
	float shaderTime = static_cast< float >( fmod( localTime, 86400.0 ) );

	//FFGL requires us to leave the context in a default state on return.
	ScopedShaderBinding shaderBinding( shader.GetGLID() );

	shader.Set( "Time", shaderTime );
	shader.Set( "Level", level );
	shader.Set( "Pattern", pattern );
	shader.Set( "Chunk", chunk );
	shader.Set( "Cycle", cycle );
	shader.Set( "Solid", solid );

	quad.Draw();

	return FF_SUCCESS;
}
FFResult FableVideoMusic::DeInitGL()
{
	shader.FreeGLResources();
	quad.Release();

	return FF_SUCCESS;
}

FFResult FableVideoMusic::SetFloatParameter( unsigned int dwIndex, float value )
{
	switch( dwIndex )
	{
	case PT_LEVEL:
		level = value;
		break;
	case PT_PATTERN:
		pattern = value;
		break;
	case PT_CHUNK:
		chunk = value;
		break;
	case PT_CYCLE:
		cycle = value;
		break;
	case PT_SOLID:
		solid = value;
		break;

	default:
		return FF_FAIL;
	}

	return FF_SUCCESS;
}

float FableVideoMusic::GetFloatParameter( unsigned int index )
{
	switch( index )
	{
	case PT_LEVEL:
		return level;
	case PT_PATTERN:
		return pattern;
	case PT_CHUNK:
		return chunk;
	case PT_CYCLE:
		return cycle;
	case PT_SOLID:
		return solid;
	}

	return 0.0f;
}
