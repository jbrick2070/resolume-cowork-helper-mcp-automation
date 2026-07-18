#pragma once
#include <FFGLSDK.h>

/// React Gate - 1895 film projection homage.
/// Recreates the mechanical film gate of early cinema: gate weave, vertical
/// judder slips, procedural dust and hairs, shutter flicker, era grading
/// (nitrate / silver / super8), animated grain and trembling frame lines.
class ReactGate : public CFFGLPlugin
{
public:
	ReactGate();
	~ReactGate();

	//CFFGLPlugin
	FFResult InitGL( const FFGLViewportStruct* vp ) override;
	FFResult ProcessOpenGL( ProcessOpenGLStruct* pGL ) override;
	FFResult DeInitGL() override;

	FFResult SetFloatParameter( unsigned int dwIndex, float value ) override;
	float GetFloatParameter( unsigned int index ) override;

private:
	ffglex::FFGLShader shader;  //!< Compiles and links the gate shader program.
	ffglex::FFGLScreenQuad quad;//!< Renders a full screen quad.

	float weave;    //!< 0-1, slow sinusoidal frame drift amplitude.
	float judder;   //!< 0-1, probability/strength of vertical frame slips.
	float dust;     //!< 0-1, amount of dust specks and gate hairs.
	float flicker;  //!< 0-1, shutter luminance flicker depth.
	float era;      //!< 0-1, film stock era: nitrate / silver / super8.
	float grain;    //!< 0-1, animated film grain strength.
	float mixAmount;//!< 0-1, dry/wet mix.

	double lastHostTime;//!< hostTime value seen on the previous frame.
	double localTime;   //!< Accumulated plugin clock in seconds.
};
