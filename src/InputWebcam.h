#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>
#include "InputVideo.h"

using namespace std;

class InputWebcam : public InputVideo{

public:
	InputWebcam();
	virtual ~InputWebcam();
	virtual bool SelSrcFile(const HWND &hParentWnd);
	virtual bool GetNextFrame(cv::Mat &frame);
	virtual bool isBegin() {
		return false; // always false
	};
	virtual void SetTempo(int tempo) {
		// do nothing
	};
	virtual double GetNextFPS(double curFPS) {
		return curFPS;
	};
private:
	cv::VideoCapture m_cap;
};
