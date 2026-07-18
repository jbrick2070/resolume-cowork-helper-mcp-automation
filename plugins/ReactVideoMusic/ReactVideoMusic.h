#pragma once
#include <FFGLSDK.h>

/// React Video Music - 1977 Atari Video Music homage (SOURCE plugin, no inputs).
/// Draws hard-edged 70s raster patterns on black: nested diamonds, vertical
/// bars, concentric rectangles or split mirror diamonds, driven by a Level
/// parameter meant to be FFT-linked in Resolume. A fixed 8-color saturated
/// palette rotates over time; coordinates quantize to a chunky coarse grid.
class ReactVideoMusic : public CFFGLPlugin
{
public:
	ReactVideoMusic();
	~ReactVideoMusic();

	//CFFGLPlugin
	FFResult InitGL( const FFGLViewportStruct* vp ) override;
	FFResult ProcessOpenGL( ProcessOpenGLStruct* pGL ) override;
	FFResult DeInitGL() override;

	FFResult SetFloatParameter( unsigned int dwIndex, float value ) override;
	float GetFloatParameter( unsigned int index ) override;

private:
	ffglex::FFGLShader shader;  //!< Compiles and links the pattern shader program.
	ffglex::FFGLScreenQuad quad;//!< Renders a full screen quad.

	float level;  //!< 0-1, THE driver - shape scale; FFT-link this in Resolume.
	float pattern;//!< 0-1, selects 1 of 4 modes: diamonds / bars / rectangles / mirror diamonds.
	float chunk;  //!< 0-1, quantizes coordinates to an 8-40 cell grid.
	float cycle;  //!< 0-1, palette rotation speed through the fixed 8-color 70s palette.
	float solid;  //!< 0-1, fill vs outline balance.

	double lastHostTime;//!< hostTime value seen on the previous frame.
	double localTime;   //!< Accumulated plugin clock in seconds.
};
