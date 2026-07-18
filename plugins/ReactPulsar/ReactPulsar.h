#pragma once
#include <FFGLSDK.h>

/// React Pulsar - 1967, the lighthouse in the noise (SOURCE plugin, no inputs).
/// CP1919 stacked-ridgeline identity, rendered STATELESS: every frame draws the
/// full stack procedurally - line i = deterministic noise profile f(row_seed,
/// t - i*P) - so no feedback buffer exists (single-pass GLSL law). The front
/// line is born at the bottom and the history recedes upward; front silhouettes
/// occlude the curves behind them. FFT enters via 0-1 scalars only.
class ReactPulsar : public CFFGLPlugin
{
public:
	ReactPulsar();
	~ReactPulsar();

	//CFFGLPlugin
	FFResult InitGL( const FFGLViewportStruct* vp ) override;
	FFResult ProcessOpenGL( ProcessOpenGLStruct* pGL ) override;
	FFResult DeInitGL() override;

	FFResult SetFloatParameter( unsigned int dwIndex, float value ) override;
	float GetFloatParameter( unsigned int index ) override;

private:
	ffglex::FFGLShader shader;  //!< Compiles and links the ridgeline shader program.
	ffglex::FFGLScreenQuad quad;//!< Renders a full screen quad.

	float level;     //!< 0-1, global amplitude - the plot breathes; FFT-link this in Resolume.
	float flux;      //!< 0-1, temporal jitter/energy - the plasma lives.
	float period;    //!< 0-1, log scroll rate 0.5-30 lines/s (placard cites the real 1.4 ms-1.34 s range).
	float stack;     //!< 0-1, number of stacked lines, 8-80.
	float beam;      //!< 0-1, line width 1.5-6 px and core gain 0.7-1.6.
	float dispersion;//!< 0-1, per-line low-order subpulse smear (DM homage).
	float glow;      //!< 0-1, exponential halo radius around each line.

	double lastHostTime;//!< hostTime value seen on the previous frame.
	double localTime;   //!< Accumulated plugin clock in seconds.
	double phaseAcc;    //!< Scroll phase integrated CPU-side in double: live Period
	                    //!< changes stay smooth (no Time*rate jump) and float
	                    //!< precision cannot quantize the scroll on overnight runs.
};
