#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>
#include "InputVideo.h"

using namespace std;

class InputWebcam : public InputVideo{

public:
	InputWebcam(HWND hParentWnd) : InputVideo(hParentWnd) {};
	virtual ~InputWebcam();
	virtual bool SelFile();
	virtual bool LoadFile();
	virtual bool GetNextFrame(cv::Mat &frame);
	virtual bool isBegin() {
		return false; // always false
	};
private:
	cv::VideoCapture m_cap;
};
