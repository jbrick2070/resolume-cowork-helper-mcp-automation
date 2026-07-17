#include "FableGate.h"
#include <cmath>
using namespace ffglex;

enum ParamType : FFUInt32
{
	PT_WEAVE,
	PT_JUDDER,
	PT_DUST,
	PT_FLICKER,
	PT_ERA,
	PT_GRAIN,
	PT_MIX
};

static CFFGLPluginInfo PluginInfo(
	PluginFactory< FableGate >,                                                    // Create method
	"FGTE",                                                                        // Plugin unique ID of maximum length 4.
	"Fable Gate",                                                                  // Plugin name
	2,                                                                             // API major version number
	1,                                                                             // API minor version number
	1,                                                                             // Plugin major version number
	0,                                                                             // Plugin minor version number
	FF_EFFECT,                                                                     // Plugin type
	"1895 - the film gate: weave, judder, dust and flicker of mechanical cinema.", // Plugin description
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
uniform float Weave;
uniform float Judder;
uniform float Dust;
uniform float Flicker;
uniform float Era;
uniform float Grain;
uniform float MixVal;

in vec2 uv;

out vec4 fragColor;

float hash11( float p )
{
	p = fract( p * 0.1031 );
	p *= p + 33.33;
	p *= p + p;
	return fract( p );
}
float hash21( vec2 p )
{
	vec3 p3 = fract( vec3( p.xyx ) * 0.1031 );
	p3 += dot( p3, p3.yzx + 33.33 );
	return fract( ( p3.x + p3.y ) * p3.z );
}
//1D value noise, smooth over time.
float vnoise1( float x )
{
	float i = floor( x );
	float f = fract( x );
	float u = f * f * ( 3.0 - 2.0 * f );
	return mix( hash11( i ), hash11( i + 1.0 ), u );
}

//Sample straight (unpremultiplied) color; outside the 0-1 frame is the black gate aperture.
vec4 gateSample( vec2 p )
{
	if( p.x < 0.0 || p.x > 1.0 || p.y < 0.0 || p.y > 1.0 )
		return vec4( 0.0 );
	vec4 c = texture( InputTexture, p * MaxUV );
	if( c.a > 0.0 )
		c.rgb /= c.a;
	return c;
}

void main()
{
	vec2 norm = uv / MaxUV;

	//--- Weave: two incommensurate sinusoidal LFOs drift the frame in x and y. ---
	float wAmp = Weave * 0.015;
	vec2 weaveOff = vec2(
		sin( Time * 0.83 ) * 0.75 + sin( Time * 2.19 ) * 0.25,
		sin( Time * 0.61 ) * 0.70 + sin( Time * 1.87 ) * 0.30 ) * wAmp;

	//--- Judder: occasional vertical frame slips per ~0.4s time bucket. ---
	float bucket = floor( Time / 0.4 );
	float judderOff = 0.0;
	if( hash11( bucket + 17.31 ) < Judder * 0.3 )
		judderOff = hash11( bucket + 91.7 ) * 0.04;

	vec2 samplePos = norm + weaveOff + vec2( 0.0, judderOff );

	//--- Era weights: 0-0.33 nitrate, 0.33-0.66 silver, 0.66-1.0 super8. ---
	float eraSeg = clamp( Era, 0.0, 1.0 ) * 3.0;
	float wNitrate = 1.0 - smoothstep( 0.8, 1.2, eraSeg );
	float wSuper8  = smoothstep( 1.8, 2.2, eraSeg );
	float wSilver  = 1.0 - wNitrate - wSuper8;

	//--- Super8 soft gate blur toward the corners (5-tap cross). ---
	float cornerDist = distance( norm, vec2( 0.5 ) );
	float blurAmt = wSuper8 * smoothstep( 0.30, 0.70, cornerDist ) * 0.0045;
	vec4 src = gateSample( samplePos );
	if( blurAmt > 0.0001 )
	{
		src += gateSample( samplePos + vec2( blurAmt, 0.0 ) );
		src += gateSample( samplePos + vec2( -blurAmt, 0.0 ) );
		src += gateSample( samplePos + vec2( 0.0, blurAmt ) );
		src += gateSample( samplePos + vec2( 0.0, -blurAmt ) );
		src /= 5.0;
	}
	vec3 col    = src.rgb;
	float alpha = src.a;

	//--- Era grading. ---
	float luma = dot( col, vec3( 0.299, 0.587, 0.114 ) );
	vec3 sepia = vec3(
		dot( col, vec3( 0.393, 0.769, 0.189 ) ),
		dot( col, vec3( 0.349, 0.686, 0.168 ) ),
		dot( col, vec3( 0.272, 0.534, 0.131 ) ) );
	vec3 silver = mix( vec3( luma ), col, 0.15 ) + vec3( 0.015, 0.030, 0.060 );
	vec3 super8 = clamp( mix( vec3( luma ), col, 1.35 ), 0.0, 1.0 ) * vec3( 1.10, 1.00, 0.90 );
	vec3 graded = sepia * wNitrate + silver * wSilver + super8 * wSuper8;

	//--- Flicker: smooth-noise luminance wobble plus a pulsing radial falloff. ---
	float flick = 1.0 + Flicker * 0.25 * ( vnoise1( Time * 11.0 ) * 2.0 - 1.0 );
	float vigBase = 0.85 * wNitrate + 0.55 * wSilver + 0.35 * wSuper8;
	float pulse = sin( Time * 5.3 ) * 0.5 + 0.5;
	float vigAmt = vigBase * ( 1.0 + Flicker * 0.20 * ( pulse - 0.5 ) );
	float vignette = 1.0 - vigAmt * smoothstep( 0.28, 0.75, cornerDist );
	graded *= flick * vignette;

	//--- Dust: hash-seeded dark specks plus an occasional gate hair near an edge. ---
	float dustMask = 0.0;
	float dustBucket = floor( Time / 0.15 );
	for( int i = 0; i < 4; ++i )
	{
		float n = dustBucket * 13.13 + float( i ) * 7.77;
		float appearChance = ( i < 2 ) ? ( Dust * 2.0 ) : ( Dust * 1.2 );
		if( hash11( n ) < appearChance )
		{
			vec2 sp = vec2( hash11( n + 1.7 ), hash11( n + 3.9 ) );
			float rad = 0.0025 + hash11( n + 5.1 ) * 0.0045;
			float d = distance( norm, sp );
			dustMask = max( dustMask, ( 1.0 - smoothstep( rad * 0.4, rad, d ) ) * ( 0.6 + 0.4 * hash11( n + 9.3 ) ) );
		}
	}
	float hairBucket = floor( Time / 0.45 );
	if( hash11( hairBucket * 3.31 + 0.7 ) < Dust * 0.45 )
	{
		float side = step( 0.5, hash11( hairBucket + 2.9 ) );
		float hx = mix( 0.035 + hash11( hairBucket + 4.2 ) * 0.10, 0.965 - hash11( hairBucket + 4.2 ) * 0.10, side );
		float wiggle = ( vnoise1( norm.y * 14.0 + hairBucket * 7.0 ) - 0.5 ) * 0.012;
		float yTop = hash11( hairBucket + 6.6 );
		float yLen = 0.25 + hash11( hairBucket + 8.8 ) * 0.55;
		float inSpan = step( yTop - yLen, norm.y ) * step( norm.y, yTop );
		float hd = abs( norm.x - ( hx + wiggle ) );
		dustMask = max( dustMask, ( 1.0 - smoothstep( 0.0006, 0.0016, hd ) ) * inSpan * 0.8 );
	}
	graded *= 1.0 - dustMask * 0.85;

	//--- Film grain: animated hash noise, strongest in the midtones. ---
	float g = hash21( norm * 1287.0 + vec2( fract( Time * 7.13 ) * 391.0, fract( Time * 11.71 ) * 271.0 ) );
	float gLuma = dot( graded, vec3( 0.299, 0.587, 0.114 ) );
	float midWeight = 0.25 + 0.75 * ( 4.0 * gLuma * ( 1.0 - gLuma ) );
	float grainMul = 1.0 + wSuper8 * 0.6;
	graded += ( g - 0.5 ) * Grain * 0.22 * midWeight * grainMul;

	//--- Frame lines: faint bars just inside top/bottom, trembling with judder. ---
	float tremor = ( hash11( bucket + 51.7 ) - 0.5 ) * 0.012 * Judder + judderOff * 0.5;
	float barH = 0.016;
	float topEdge = 1.0 - barH + tremor;
	float botEdge = barH + tremor;
	float bars = smoothstep( topEdge - 0.003, topEdge, norm.y ) + ( 1.0 - smoothstep( botEdge, botEdge + 0.003, norm.y ) );
	bars = clamp( bars, 0.0, 1.0 );
	graded *= 1.0 - bars * 0.75;

	//--- Mix and premultiply back for the video engine. ---
	graded = clamp( graded, 0.0, 1.0 );
	vec4 wet = vec4( graded * alpha, alpha );
	vec4 dry = texture( InputTexture, uv );
	vec4 mixed = mix( dry, wet, MixVal );
	mixed.rgb = clamp( mixed.rgb, vec3( 0.0 ), vec3( mixed.a ) );
	fragColor = mixed;
}
)";

FableGate::FableGate() :
	weave( 0.3f ), judder( 0.25f ), dust( 0.35f ), flicker( 0.4f ), era( 0.0f ), grain( 0.3f ), mixAmount( 1.0f ),
	lastHostTime( 0.0 ), localTime( 0.0 )
{
	SetMinInputs( 1 );
	SetMaxInputs( 1 );

	//The SDK does not initialise hostTime; zero it so our clock fallback is deterministic.
	hostTime = 0.0;

	SetParamInfo( PT_WEAVE, "Weave", FF_TYPE_STANDARD, 0.3f );
	SetParamInfo( PT_JUDDER, "Judder", FF_TYPE_STANDARD, 0.25f );
	SetParamInfo( PT_DUST, "Dust", FF_TYPE_STANDARD, 0.35f );
	SetParamInfo( PT_FLICKER, "Flicker", FF_TYPE_STANDARD, 0.4f );
	SetParamInfo( PT_ERA, "Era", FF_TYPE_STANDARD, 0.0f );
	SetParamInfo( PT_GRAIN, "Grain", FF_TYPE_STANDARD, 0.3f );
	SetParamInfo( PT_MIX, "Mix", FF_TYPE_STANDARD, 1.0f );

	FFGLLog::LogToHost( "Created Fable Gate effect" );
}
FableGate::~FableGate()
{
}

FFResult FableGate::InitGL( const FFGLViewportStruct* vp )
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
FFResult FableGate::ProcessOpenGL( ProcessOpenGLStruct* pGL )
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
	shader.Set( "Weave", weave );
	shader.Set( "Judder", judder );
	shader.Set( "Dust", dust );
	shader.Set( "Flicker", flicker );
	shader.Set( "Era", era );
	shader.Set( "Grain", grain );
	shader.Set( "MixVal", mixAmount );

	quad.Draw();

	return FF_SUCCESS;
}
FFResult FableGate::DeInitGL()
{
	shader.FreeGLResources();
	quad.Release();

	return FF_SUCCESS;
}

FFResult FableGate::SetFloatParameter( unsigned int dwIndex, float value )
{
	switch( dwIndex )
	{
	case PT_WEAVE:
		weave = value;
		break;
	case PT_JUDDER:
		judder = value;
		break;
	case PT_DUST:
		dust = value;
		break;
	case PT_FLICKER:
		flicker = value;
		break;
	case PT_ERA:
		era = value;
		break;
	case PT_GRAIN:
		grain = value;
		break;
	case PT_MIX:
		mixAmount = value;
		break;

	default:
		return FF_FAIL;
	}

	return FF_SUCCESS;
}

float FableGate::GetFloatParameter( unsigned int index )
{
	switch( index )
	{
	case PT_WEAVE:
		return weave;
	case PT_JUDDER:
		return judder;
	case PT_DUST:
		return dust;
	case PT_FLICKER:
		return flicker;
	case PT_ERA:
		return era;
	case PT_GRAIN:
		return grain;
	case PT_MIX:
		return mixAmount;
	}

	return 0.0f;
}
