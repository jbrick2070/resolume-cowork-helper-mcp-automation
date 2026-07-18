#pragma once
#include <FFGLSDK.h>

/// React Anamorphic - 1953 CinemaScope lens homage.
/// Recreates the character of anamorphic projection glass: horizontal
/// blue streak flares from thresholded highlights, de-squeeze stretch with
/// vertical-oval vignetting, radial chromatic fringing and focus breathing.
class ReactAnamorphic : public CFFGLPlugin
{
public:
	ReactAnamorphic();
	~ReactAnamorphic();

	//CFFGLPlugin
	FFResult InitGL( const FFGLViewportStruct* vp ) override;
	FFResult ProcessOpenGL( ProcessOpenGLStruct* pGL ) override;
	FFResult DeInitGL() override;

	FFResult SetFloatParameter( unsigned int dwIndex, float value ) override;
	float GetFloatParameter( unsigned int index ) override;

private:
	ffglex::FFGLShader shader;  //!< Compiles and links the anamorphic shader program.
	ffglex::FFGLScreenQuad quad;//!< Renders a full screen quad.

	float streak;   //!< 0-1, horizontal flare streak length/intensity.
	float threshold;//!< 0-1, luma threshold feeding the streak pass.
	float squeeze;  //!< 0-1, horizontal de-squeeze stretch toward 1.33x plus oval vignette.
	float fringe;   //!< 0-1, radial chromatic aberration, up to ~1.2% at edges.
	float breathe;  //!< 0-1, slow focus-breathing zoom oscillation.
	float mixAmount;//!< 0-1, dry/wet mix.

	double lastHostTime;//!< hostTime value seen on the previous frame.
	double localTime;   //!< Accumulated plugin clock in seconds.
};
