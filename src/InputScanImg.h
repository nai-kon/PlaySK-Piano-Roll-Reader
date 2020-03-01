#pragma once
#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>
#include "InputVideo.h"

using namespace std;

class InputScanImg : public InputVideo {

public:
	InputScanImg() {};
	virtual ~InputScanImg();
	virtual bool SelSrcFile(const HWND &hParentWnd);
	virtual bool GetNextFrame(cv::Mat &frame);
	virtual bool isBegin() {
		return m_dCurYPos == 0;
	};

private:
	cv::Mat m_img;
	double m_dCurYPos;
	UINT m_uiRollLeftPos;
	UINT m_uiRollRightPos;
	UINT m_uiMargin;
	UINT m_uiRollWidth;

	void FindBothEndsPos();
};
