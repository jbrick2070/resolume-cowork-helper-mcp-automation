#pragma once
#include <FFGLSDK.h>

/// Fable Scanline - Rutt-Etra style scanline displacement effect.
/// The input image is rebuilt as horizontal scanlines whose vertical position
/// is displaced by the source luminance, producing bright glowing ridges on black.
class FableScanline : public CFFGLPlugin
{
public:
	FableScanline();
	~FableScanline();

	//CFFGLPlugin
	FFResult InitGL( const FFGLViewportStruct* vp ) override;
	FFResult ProcessOpenGL( ProcessOpenGLStruct* pGL ) override;
	FFResult DeInitGL() override;

	FFResult SetFloatParameter( unsigned int dwIndex, float value ) override;
	float GetFloatParameter( unsigned int index ) override;

private:
	ffglex::FFGLShader shader;  //!< Compiles and links the scanline shader program.
	ffglex::FFGLScreenQuad quad;//!< Renders a full screen quad.

	float lines;    //!< 0-1, maps to 16-480 scanlines.
	float displace; //!< 0-1, luminance displacement strength.
	float thickness;//!< 0-1, scanline core thickness relative to line spacing.
	float glow;     //!< 0-1, soft glow falloff around each line.
	float mixAmount;//!< 0-1, dry/wet mix.
};
