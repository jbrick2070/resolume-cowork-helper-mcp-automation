#include "ReactScanline.h"
using namespace ffglex;

enum ParamType : FFUInt32
{
	PT_LINES,
	PT_DISPLACE,
	PT_THICKNESS,
	PT_GLOW,
	PT_MIX
};

static const float MIN_LINE_COUNT = 16.0f;
static const float MAX_LINE_COUNT = 480.0f;

static CFFGLPluginInfo PluginInfo(
	PluginFactory< ReactScanline >,           // Create method
	"FSCN",                                   // Plugin unique ID of maximum length 4.
	"React Scanline",                         // Plugin name
	2,                                        // API major version number
	1,                                        // API minor version number
	1,                                        // Plugin major version number
	0,                                        // Plugin minor version number
	FF_EFFECT,                                // Plugin type
	"Rutt-Etra style scanline displacement",  // Plugin description
	"React / Res_Fable rig"                   // About
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
uniform float LineCount;
uniform float Displace;
uniform float Thickness;
uniform float Glow;
uniform float MixVal;

in vec2 uv;

out vec4 fragColor;

//Sample the input and return straight (unpremultiplied) color.
vec4 sampleStraight( vec2 normPos )
{
	vec4 c = texture( InputTexture, normPos * MaxUV );
	if( c.a > 0.0 )
		c.rgb /= c.a;
	return c;
}

void main()
{
	//uv is in [0, MaxUV] texture space; norm is 0-1 content space.
	vec2 norm = uv / MaxUV;

	float N          = LineCount;
	float spacing    = 1.0 / N;
	float maxDisp    = Displace * 0.35;                       //Max upward ridge travel as screen fraction.
	float coreRadius = max( spacing * Thickness * 0.5, 1e-5 );//Sharp scanline core half width.
	float glowRadius = spacing * ( 0.5 + Glow * 4.0 );        //Wide soft skirt half width.

	//A scanline i sits at yc = (i + 0.5) / N and its ridge is displaced upward by
	//Displace * luma * 0.35. So this pixel can be lit by lines whose centers lie
	//between (y - maxDisp - glowRadius) and (y + glowRadius).
	int iLo = int( floor( ( norm.y - maxDisp - glowRadius ) * N ) );
	int iHi = int( floor( ( norm.y + glowRadius ) * N ) ) + 1;
	iLo = clamp( iLo, 0, int( N ) - 1 );
	iHi = clamp( iHi, 0, int( N ) - 1 );
	//Safety cap; keep the lines nearest the pixel (highest indices reach it soonest).
	if( iHi - iLo > 240 )
		iLo = iHi - 240;

	vec3 scanRGB = vec3( 0.0 );
	float scanA  = 0.0;

	for( int i = iLo; i <= iHi; ++i )
	{
		float yc = ( float( i ) + 0.5 ) * spacing;
		vec4 src = sampleStraight( vec2( norm.x, yc ) );
		float luma = dot( src.rgb * src.a, vec3( 0.299, 0.587, 0.114 ) );

		//Bright content pushes its scanline upward (Rutt-Etra ridge).
		float yd   = yc + Displace * luma * 0.35;
		float dist = abs( norm.y - yd );

		float core     = 1.0 - smoothstep( 0.0, coreRadius, dist );
		float skirt    = 1.0 - smoothstep( 0.0, glowRadius, dist );
		float halo     = Glow * skirt * skirt * 0.6;
		float intensity = core + halo;

		//Accumulate premultiplied-style so overlapping glows add up.
		scanRGB += src.rgb * src.a * intensity;
		scanA = max( scanA, clamp( intensity, 0.0, 1.0 ) * src.a );
	}

	scanRGB = clamp( scanRGB, vec3( 0.0 ), vec3( 1.0 ) );
	scanA   = clamp( scanA, 0.0, 1.0 );

	//Original pixel stays premultiplied; scanline result is already premultiplied.
	vec4 orig  = texture( InputTexture, uv );
	vec4 mixed = mix( orig, vec4( scanRGB, scanA ), MixVal );

	//Output must be premultiplied and inside the LDR range the video engine works in.
	mixed.rgb = clamp( mixed.rgb, vec3( 0.0 ), vec3( mixed.a ) );
	fragColor = mixed;
}
)";

ReactScanline::ReactScanline() :
	lines( 0.25f ), displace( 0.35f ), thickness( 0.5f ), glow( 0.4f ), mixAmount( 1.0f )
{
	SetMinInputs( 1 );
	SetMaxInputs( 1 );

	SetParamInfo( PT_LINES, "Lines", FF_TYPE_STANDARD, 0.25f );
	SetParamInfo( PT_DISPLACE, "Displace", FF_TYPE_STANDARD, 0.35f );
	SetParamInfo( PT_THICKNESS, "Thickness", FF_TYPE_STANDARD, 0.5f );
	SetParamInfo( PT_GLOW, "Glow", FF_TYPE_STANDARD, 0.4f );
	SetParamInfo( PT_MIX, "Mix", FF_TYPE_STANDARD, 1.0f );

	FFGLLog::LogToHost( "Created React Scanline effect" );
}
ReactScanline::~ReactScanline()
{
}

FFResult ReactScanline::InitGL( const FFGLViewportStruct* vp )
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
FFResult ReactScanline::ProcessOpenGL( ProcessOpenGLStruct* pGL )
{
	if( pGL->numInputTextures < 1 )
		return FF_FAIL;

	if( pGL->inputTextures[ 0 ] == NULL )
		return FF_FAIL;

	//FFGL requires us to leave the context in a default state on return.
	ScopedShaderBinding shaderBinding( shader.GetGLID() );
	ScopedSamplerActivation activateSampler( 0 );
	Scoped2DTextureBinding textureBinding( pGL->inputTextures[ 0 ]->Handle );

	shader.Set( "InputTexture", 0 );

	FFGLTexCoords maxCoords = GetMaxGLTexCoords( *pGL->inputTextures[ 0 ] );
	shader.Set( "MaxUV", maxCoords.s, maxCoords.t );

	float lineCount = MIN_LINE_COUNT + lines * ( MAX_LINE_COUNT - MIN_LINE_COUNT );
	shader.Set( "LineCount", lineCount );
	shader.Set( "Displace", displace );
	shader.Set( "Thickness", thickness );
	shader.Set( "Glow", glow );
	shader.Set( "MixVal", mixAmount );

	quad.Draw();

	return FF_SUCCESS;
}
FFResult ReactScanline::DeInitGL()
{
	shader.FreeGLResources();
	quad.Release();

	return FF_SUCCESS;
}

FFResult ReactScanline::SetFloatParameter( unsigned int dwIndex, float value )
{
	switch( dwIndex )
	{
	case PT_LINES:
		lines = value;
		break;
	case PT_DISPLACE:
		displace = value;
		break;
	case PT_THICKNESS:
		thickness = value;
		break;
	case PT_GLOW:
		glow = value;
		break;
	case PT_MIX:
		mixAmount = value;
		break;

	default:
		return FF_FAIL;
	}

	return FF_SUCCESS;
}

float ReactScanline::GetFloatParameter( unsigned int index )
{
	switch( index )
	{
	case PT_LINES:
		return lines;
	case PT_DISPLACE:
		return displace;
	case PT_THICKNESS:
		return thickness;
	case PT_GLOW:
		return glow;
	case PT_MIX:
		return mixAmount;
	}

	return 0.0f;
}
