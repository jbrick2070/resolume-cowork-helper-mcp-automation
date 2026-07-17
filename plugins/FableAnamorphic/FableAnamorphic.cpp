#include "FableAnamorphic.h"
#include <cmath>
using namespace ffglex;

enum ParamType : FFUInt32
{
	PT_STREAK,
	PT_THRESHOLD,
	PT_SQUEEZE,
	PT_FRINGE,
	PT_BREATHE,
	PT_MIX
};

static CFFGLPluginInfo PluginInfo(
	PluginFactory< FableAnamorphic >,                                              // Create method
	"FANA",                                                                        // Plugin unique ID of maximum length 4.
	"Fable Anamorphic",                                                            // Plugin name
	2,                                                                             // API major version number
	1,                                                                             // API minor version number
	1,                                                                             // Plugin major version number
	0,                                                                             // Plugin minor version number
	FF_EFFECT,                                                                     // Plugin type
	"1953 - CinemaScope anamorphic glass: streak flares, oval bokeh, fringed edges.", // Plugin description
	"Fable / Res_Fable rig"                                                        // About
);

static const char _vertexShaderCode[] = R"(#version 410 core
uniform vec2 MaxUV;

layout( location = 0 ) in vec4 vPosition;
layout( location = 1 ) in vec2 vUV;

out vec2 uv;

void main()
{
	gl_Position = vPosition;
	uv = vUV * MaxUV;
}
)";

static const char _fragmentShaderCode[] = R"(#version 410 core
uniform sampler2D InputTexture;
uniform vec2 MaxUV;
uniform float Time;
uniform float Streak;
uniform float Threshold;
uniform float Squeeze;
uniform float Fringe;
uniform float Breathe;
uniform float MixVal;

in vec2 uv;

out vec4 fragColor;

//Sample premultiplied color, edge-clamped in 0-1 content space.
vec4 sampleClamped( vec2 p )
{
	p = clamp( p, vec2( 0.0 ), vec2( 1.0 ) );
	return texture( InputTexture, p * MaxUV );
}

void main()
{
	vec2 norm = uv / MaxUV;
	vec2 center = vec2( 0.5 );

	//--- Breathe: slow focus-breathing zoom, ~0.15 Hz, up to 0.5% at max. ---
	float breatheScale = 1.0 + Breathe * 0.005 * sin( Time * 0.9425 );

	//--- Squeeze: horizontal de-squeeze stretch toward 1.33x at max. ---
	float squeezeScale = 1.0 + Squeeze * 0.33;
	vec2 p = center + ( norm - center ) / vec2( squeezeScale * breatheScale, breatheScale );

	//--- Fringe: radial chromatic aberration growing with distance from center. ---
	vec2 dir = p - center;
	vec2 caOff = dir * ( Fringe * 0.024 * length( dir ) );
	vec4 srcG = sampleClamped( p );
	float srcR = sampleClamped( p + caOff ).r;
	float srcB = sampleClamped( p - caOff ).b;
	vec3 base = vec3( srcR, srcG.g, srcB );//Premultiplied RGB with fringed edges.
	float alpha = srcG.a;

	//--- Streak: horizontal box blur of the thresholded brights, tinted cool blue. ---
	vec3 streakSum = vec3( 0.0 );
	float halfLen = Streak * 0.22 + 0.01;
	for( int i = -12; i <= 12; ++i )
	{
		float t = float( i ) / 12.0;
		vec3 s = sampleClamped( vec2( p.x + t * halfLen, p.y ) ).rgb;
		float l = dot( s, vec3( 0.299, 0.587, 0.114 ) );
		float bright = max( l - Threshold, 0.0 ) / max( 1.0 - Threshold, 0.05 );
		streakSum += s * bright;
	}
	//Cool blue anamorphic tint (#66AAFF).
	vec3 streakCol = ( streakSum / 25.0 ) * vec3( 0.40, 0.667, 1.0 ) * ( Streak * 2.2 );
	streakCol = clamp( streakCol, vec3( 0.0 ), vec3( 1.0 ) );

	//Screen-blend the streaks over the image; streaks also glow over transparency.
	vec3 col = 1.0 - ( 1.0 - base ) * ( 1.0 - streakCol );
	float streakA = max( streakCol.r, max( streakCol.g, streakCol.b ) );
	float outA = max( alpha, streakA );

	//--- Vertical-oval vignette shaping that follows the squeeze. ---
	vec2 vd = ( norm - center ) * vec2( 1.0 + Squeeze * 0.9, 1.0 );
	col *= 1.0 - Squeeze * 0.35 * smoothstep( 0.32, 0.72, length( vd ) );

	//--- Mix; output stays premultiplied for the video engine. ---
	col = clamp( col, vec3( 0.0 ), vec3( outA ) );
	vec4 wet = vec4( col, outA );
	vec4 dry = texture( InputTexture, uv );
	vec4 mixed = mix( dry, wet, MixVal );
	mixed.rgb = clamp( mixed.rgb, vec3( 0.0 ), vec3( mixed.a ) );
	fragColor = mixed;
}
)";

FableAnamorphic::FableAnamorphic() :
	streak( 0.5f ), threshold( 0.7f ), squeeze( 0.3f ), fringe( 0.35f ), breathe( 0.2f ), mixAmount( 1.0f ),
	lastHostTime( 0.0 ), localTime( 0.0 )
{
	SetMinInputs( 1 );
	SetMaxInputs( 1 );

	//The SDK does not initialise hostTime; zero it so our clock fallback is deterministic.
	hostTime = 0.0;

	SetParamInfo( PT_STREAK, "Streak", FF_TYPE_STANDARD, 0.5f );
	SetParamInfo( PT_THRESHOLD, "Threshold", FF_TYPE_STANDARD, 0.7f );
	SetParamInfo( PT_SQUEEZE, "Squeeze", FF_TYPE_STANDARD, 0.3f );
	SetParamInfo( PT_FRINGE, "Fringe", FF_TYPE_STANDARD, 0.35f );
	SetParamInfo( PT_BREATHE, "Breathe", FF_TYPE_STANDARD, 0.2f );
	SetParamInfo( PT_MIX, "Mix", FF_TYPE_STANDARD, 1.0f );

	FFGLLog::LogToHost( "Created Fable Anamorphic effect" );
}
FableAnamorphic::~FableAnamorphic()
{
}

FFResult FableAnamorphic::InitGL( const FFGLViewportStruct* vp )
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
FFResult FableAnamorphic::ProcessOpenGL( ProcessOpenGLStruct* pGL )
{
	if( pGL->numInputTextures < 1 )
		return FF_FAIL;

	if( pGL->inputTextures[ 0 ] == NULL )
		return FF_FAIL;

	//Advance the plugin clock: prefer host-provided time (SetTime), fall back to a 60 fps step.
	double delta = hostTime - lastHostTime;
	if( delta <= 0.0 || delta > 0.5 )
		delta = 1.0 / 60.0;
	localTime += delta;
	lastHostTime = hostTime;
	float shaderTime = static_cast< float >( fmod( localTime, 86400.0 ) );

	//FFGL requires us to leave the context in a default state on return.
	ScopedShaderBinding shaderBinding( shader.GetGLID() );
	ScopedSamplerActivation activateSampler( 0 );
	Scoped2DTextureBinding textureBinding( pGL->inputTextures[ 0 ]->Handle );

	shader.Set( "InputTexture", 0 );

	FFGLTexCoords maxCoords = GetMaxGLTexCoords( *pGL->inputTextures[ 0 ] );
	shader.Set( "MaxUV", maxCoords.s, maxCoords.t );

	shader.Set( "Time", shaderTime );
	shader.Set( "Streak", streak );
	shader.Set( "Threshold", threshold );
	shader.Set( "Squeeze", squeeze );
	shader.Set( "Fringe", fringe );
	shader.Set( "Breathe", breathe );
	shader.Set( "MixVal", mixAmount );

	quad.Draw();

	return FF_SUCCESS;
}
FFResult FableAnamorphic::DeInitGL()
{
	shader.FreeGLResources();
	quad.Release();

	return FF_SUCCESS;
}

FFResult FableAnamorphic::SetFloatParameter( unsigned int dwIndex, float value )
{
	switch( dwIndex )
	{
	case PT_STREAK:
		streak = value;
		break;
	case PT_THRESHOLD:
		threshold = value;
		break;
	case PT_SQUEEZE:
		squeeze = value;
		break;
	case PT_FRINGE:
		fringe = value;
		break;
	case PT_BREATHE:
		breathe = value;
		break;
	case PT_MIX:
		mixAmount = value;
		break;

	default:
		return FF_FAIL;
	}

	return FF_SUCCESS;
}

float FableAnamorphic::GetFloatParameter( unsigned int index )
{
	switch( index )
	{
	case PT_STREAK:
		return streak;
	case PT_THRESHOLD:
		return threshold;
	case PT_SQUEEZE:
		return squeeze;
	case PT_FRINGE:
		return fringe;
	case PT_BREATHE:
		return breathe;
	case PT_MIX:
		return mixAmount;
	}

	return 0.0f;
}
