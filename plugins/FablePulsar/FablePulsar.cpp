#include "FablePulsar.h"
#include <cmath>
using namespace ffglex;

enum ParamType : FFUInt32
{
	PT_LEVEL,
	PT_FLUX,
	PT_PERIOD,
	PT_STACK,
	PT_BEAM,
	PT_DISPERSION,
	PT_GLOW
};

static CFFGLPluginInfo PluginInfo(
	PluginFactory< FablePulsar >,                                                  // Create method
	"FPLS",                                                                        // Plugin unique ID of maximum length 4.
	"Fable Pulsar",                                                                // Plugin name
	2,                                                                             // API major version number
	1,                                                                             // API minor version number
	1,                                                                             // Plugin major version number
	0,                                                                             // Plugin minor version number
	FF_SOURCE,                                                                     // Plugin type
	"1967 - the lighthouse in the noise. CP1919 stacked ridgelines, stateless.",   // Plugin description
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
uniform float Flux;
uniform float PhaseK;
uniform float PhaseF;
uniform float Stack;
uniform float Beam;
uniform float Dispersion;
uniform float Glow;
uniform vec2 Resolution;

in vec2 uv;

out vec4 fragColor;

//Integer hashes. Every caller passes integral-valued floats, so the int cast
//is exact and a CPU reimplementation of uint(int(n) & 0x7fffffff) agrees
//bit-for-bit for |n| < 2^31. The mask maps negative seeds into positive space.
float hash11( float n )
{
	uint x = uint( int( n ) & 0x7fffffff );
	x ^= x >> 16u;
	x *= 0x7feb352du;
	x ^= x >> 15u;
	x *= 0x846ca68bu;
	x ^= x >> 16u;
	return float( x & 0x00ffffffu ) / 16777215.0;
}

float hash13( vec3 p )
{
	uint x = uint( int( p.x ) & 0x7fffffff );
	uint y = uint( int( p.y ) & 0x7fffffff );
	uint z = uint( int( p.z ) & 0x7fffffff );
	uint h = ( x * 0x8da6b343u ) ^ ( y * 0xd8163841u ) ^ ( z * 0xcb1ab31fu );
	h ^= h >> 13u;
	h *= 0x7feb352du;
	h ^= h >> 16u;
	return float( h & 0x00ffffffu ) / 16777215.0;
}

//Value noise in [0,1]. Lattice coordinates are integral so hash13 stays exact.
float vnoise( vec2 p, float seed )
{
	vec2 ip = floor( p );
	vec2 fp = fract( p );
	vec2 u = fp * fp * ( 3.0 - 2.0 * fp );
	float a = hash13( vec3( ip.x, ip.y, seed ) );
	float b = hash13( vec3( ip.x + 1.0, ip.y, seed ) );
	float c = hash13( vec3( ip.x, ip.y + 1.0, seed ) );
	float d = hash13( vec3( ip.x + 1.0, ip.y + 1.0, seed ) );
	return mix( mix( a, b, u.x ), mix( c, d, u.x ), u.y );
}

//Edge window: pulses live in the middle of the trace. Edge order is FIXED
//ascending per GLSL 4.10 (reversed-edge smoothstep is undefined behavior).
float W( float x )
{
	return smoothstep( 0.18, 0.30, x ) * ( 1.0 - smoothstep( 0.70, 0.82, x ) );
}

//Subpulse profile for the line with seed s at horizontal position x:
//M = 3 gaussians whose SHAPE per (s, x) is eternal - only amplitude breathes.
float profileP( float s, float x, float disp )
{
	float sum = 0.0;
	for( int j = 0; j < 3; ++j )
	{
		float fj = float( j );
		float Aj = 0.3 + 0.7 * hash13( vec3( s, fj, 1.0 ) );
		float cj = 0.5 + 0.18 * ( hash13( vec3( s, fj, 2.0 ) ) - 0.5 )
				   + disp * 0.12 * ( 1.0 - Aj ) * ( fj - 1.0 );
		float wj = mix( 0.008, 0.045, hash13( vec3( s, fj, 3.0 ) ) );
		float t = ( x - cj ) / wj;
		sum += Aj * exp( -t * t );
	}
	return W( x ) * sum;
}

void main()
{
	//Scroll phase arrives pre-integrated from the CPU (double accumulator):
	//live Period changes stay smooth and float precision cannot quantize the
	//scroll on overnight runs. PhaseK is the integral part (line counter,
	//wrapped at 2^23 - float-exact), PhaseF the fractional scroll position
	//in [0,1). Seeds below wrap with the SAME modulus, so the wrap is
	//seamless: no full-stack reseed, ever.
	float k = PhaseK;
	float f = PhaseF;
	int N = int( round( mix( 8.0, 80.0, clamp( Stack, 0.0, 1.0 ) ) ) );

	const float hMax = 0.22;
	float resY = max( Resolution.y, 1.0 );
	float beamW = mix( 1.5, 6.0, clamp( Beam, 0.0, 1.0 ) ) / resY;
	float coreGain = mix( 0.7, 1.6, clamp( Beam, 0.0, 1.0 ) );
	float glowR = clamp( Glow, 0.0, 1.0 ) * 0.02 + 0.002;
	float glowReach = glowR * 4.0 + beamW;
	float lineGap = 0.6 / float( N + 1 );
	float disp = clamp( Dispersion, 0.0, 1.0 );

	//Line i = 0 carries the NEWEST seed (s = k) and sits at the BOTTOM: new
	//pulses are born at the front and the history recedes upward, the classic
	//animated CP1919 scroll. Iterating i upward walks front to back, so the
	//first line that owns a pixel occludes every line behind it.
	vec3 col = vec3( 0.0 );

	//Lines whose maximum reach (baseline + hMax + glow) is below this pixel
	//can never touch it: start at the first line that can. This keeps the
	//per-pixel cost at a handful of profile evaluations, not N.
	int iStart = int( max( 0.0, floor( ( uv.y - hMax - glowReach ) * float( N + 1 ) - f - 0.5 ) ) );

	for( int i = iStart; i < N; ++i )
	{
		float yB = ( float( i ) + f + 0.5 ) / float( N + 1 );

		//This strip and every strip behind it start above the pixel: the
		//pixel lives in the silhouette gap. Keep any glow already collected.
		if( yB - lineGap > uv.y )
			break;

		//Conservative early reject before paying for the profile.
		if( uv.y > yB + hMax + glowReach )
			continue;

		//Seed wraps with the same modulus as PhaseK: near the wrap k - i goes
		//negative and mod() folds it back to the top of the seed domain, so
		//every line keeps its identity across the wrap (GLSL mod is
		//non-negative for a positive modulus).
		float s = mod( k - float( i ), 8388608.0 );
		float p = profileP( s, uv.x, disp );

		//Amplitude: Level breathes the whole plot, Flux adds temporal jitter.
		//Determinism contract: subpulse SHAPE per (s, x) is eternal, the
		//amplitude lives (the plasma breathes).
		float Hs = max( 0.0, Level * ( 0.55 + 0.45 * hash11( s ) )
				   + Flux * 0.25 * ( vnoise( vec2( uv.x * 7.0, Time * 2.0 ), s ) - 0.5 ) );
		float yC = yB + clamp( p * Hs, 0.0, 1.0 ) * hMax;

		//Above this line's glow: the pixel belongs to a line further back.
		if( uv.y > yC + glowReach )
			continue;

		float d = abs( uv.y - yC );
		float core = ( 1.0 - smoothstep( 0.0, beamW, d ) ) * coreGain;
		float glowV = exp( -d / glowR ) * 0.35;
		col = max( col, vec3( core + glowV ) );

		//Ownership: between the silhouette floor and the beam top - this
		//line's card occludes everything behind it, black body included.
		if( uv.y >= yB - lineGap && uv.y <= yC + beamW )
			break;
	}

	//SOURCE plugin: opaque black background, premultiplied-safe.
	fragColor = vec4( col, 1.0 );
}
)";

FablePulsar::FablePulsar() :
	level( 0.6f ), flux( 0.25f ), period( 0.45f ), stack( 0.5f ), beam( 0.5f ),
	dispersion( 0.2f ), glow( 0.35f ),
	lastHostTime( 0.0 ), localTime( 0.0 ), phaseAcc( 0.0 )
{
	//This is a source plugin: no input textures.
	SetMinInputs( 0 );
	SetMaxInputs( 0 );

	//The SDK does not initialise hostTime; zero it so our clock fallback is deterministic.
	hostTime = 0.0;

	SetParamInfo( PT_LEVEL, "Level", FF_TYPE_STANDARD, 0.6f );
	SetParamInfo( PT_FLUX, "Flux", FF_TYPE_STANDARD, 0.25f );
	SetParamInfo( PT_PERIOD, "Period", FF_TYPE_STANDARD, 0.45f );
	SetParamInfo( PT_STACK, "Stack", FF_TYPE_STANDARD, 0.5f );
	SetParamInfo( PT_BEAM, "Beam", FF_TYPE_STANDARD, 0.5f );
	SetParamInfo( PT_DISPERSION, "Dispersion", FF_TYPE_STANDARD, 0.2f );
	SetParamInfo( PT_GLOW, "Glow", FF_TYPE_STANDARD, 0.35f );

	FFGLLog::LogToHost( "Created Fable Pulsar source" );
}
FablePulsar::~FablePulsar()
{
}

FFResult FablePulsar::InitGL( const FFGLViewportStruct* vp )
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
FFResult FablePulsar::ProcessOpenGL( ProcessOpenGLStruct* pGL )
{
	//Advance the plugin clock: prefer host-provided time (SetTime), fall back to a 60 fps step.
	double delta = hostTime - lastHostTime;
	if( delta <= 0.0 || delta > 0.5 )
		delta = 1.0 / 60.0;
	localTime += delta;
	lastHostTime = hostTime;
	float shaderTime = static_cast< float >( fmod( localTime, 86400.0 ) );

	//Integrate scroll phase in double at the CURRENT rate: log-spaced
	//0.5..30 lines/sec (VISUAL range; the placard cites the real
	//1.4 ms .. 1.34 s pulsar periods). Integration - not Time * rate -
	//keeps live Period sweeps smooth and overnight runs precise.
	const double p = ( period < 0.0f ) ? 0.0 : ( ( period > 1.0f ) ? 1.0 : static_cast< double >( period ) );
	const double rate = exp( ( 1.0 - p ) * log( 0.5 ) + p * log( 30.0 ) );
	phaseAcc += delta * rate;
	//Keep the accumulator bounded (fract precision stays maximal forever).
	//Folding at the seed modulus preserves both k mod 2^23 and the fract.
	if( phaseAcc >= 8388608.0 )
		phaseAcc = fmod( phaseAcc, 8388608.0 );
	//2^23: float-exact, and the shader wraps seeds with the same modulus so
	//the wrap is seamless (no full-stack reseed).
	const double kWhole = floor( phaseAcc );
	const float phaseK = static_cast< float >( fmod( kWhole, 8388608.0 ) );
	const float phaseF = static_cast< float >( phaseAcc - kWhole );

	//FFGL requires us to leave the context in a default state on return.
	ScopedShaderBinding shaderBinding( shader.GetGLID() );

	shader.Set( "Time", shaderTime );
	shader.Set( "Level", level );
	shader.Set( "Flux", flux );
	shader.Set( "PhaseK", phaseK );
	shader.Set( "PhaseF", phaseF );
	shader.Set( "Stack", stack );
	shader.Set( "Beam", beam );
	shader.Set( "Dispersion", dispersion );
	shader.Set( "Glow", glow );
	shader.Set( "Resolution",
				static_cast< float >( currentViewport.width ),
				static_cast< float >( currentViewport.height ) );

	quad.Draw();

	return FF_SUCCESS;
}
FFResult FablePulsar::DeInitGL()
{
	shader.FreeGLResources();
	quad.Release();

	return FF_SUCCESS;
}

FFResult FablePulsar::SetFloatParameter( unsigned int dwIndex, float value )
{
	switch( dwIndex )
	{
	case PT_LEVEL:
		level = value;
		break;
	case PT_FLUX:
		flux = value;
		break;
	case PT_PERIOD:
		period = value;
		break;
	case PT_STACK:
		stack = value;
		break;
	case PT_BEAM:
		beam = value;
		break;
	case PT_DISPERSION:
		dispersion = value;
		break;
	case PT_GLOW:
		glow = value;
		break;

	default:
		return FF_FAIL;
	}

	return FF_SUCCESS;
}

float FablePulsar::GetFloatParameter( unsigned int index )
{
	switch( index )
	{
	case PT_LEVEL:
		return level;
	case PT_FLUX:
		return flux;
	case PT_PERIOD:
		return period;
	case PT_STACK:
		return stack;
	case PT_BEAM:
		return beam;
	case PT_DISPERSION:
		return dispersion;
	case PT_GLOW:
		return glow;
	}

	return 0.0f;
}
