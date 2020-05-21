#pragma once
#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>
#include "InputVideo.h"

using namespace std;

class InputScanImg : public InputVideo {

public:
	InputScanImg();
	virtual ~InputScanImg();
	virtual bool SelSrcFile(const HWND &hParentWnd);
	virtual bool GetNextFrame(cv::Mat &frame);
	virtual bool isBegin() {
		return m_uiCurYPos == 0;
	};
	void SetTempo(int tempo);
	double GetNextFPS(double curFPS);
	void SetSpoolDiameter(double diameter) {
		m_dOrgSpoolDiameter = m_dCurSpoolDiameter = diameter;
	}

private:
	cv::Mat m_img;
	UINT m_uiCurYPos;
	UINT m_uiSkipPxs;
	UINT m_uiRollLeftPos;
	UINT m_uiRollRightPos;
	UINT m_udMargin;
	UINT m_uiRollWidth; 
	double m_dDPI;
	double m_dRollAbsWidth = 11.25;			// in inch
	double m_dRollThickness = 0.00334646;	// in inch
	double m_dOrgSpoolDiameter;	// in inch
	double m_dCurSpoolDiameter; // in inch
	double m_dSpoolRPS;			// round per sec
	double m_dCurSpoolPos;		// between 0.0 - 1.0 (0 - 360 degree)

	void FindRollEdges();
};
