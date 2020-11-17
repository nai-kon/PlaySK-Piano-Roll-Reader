#pragma once
#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>
#include "InputVideo.h"

using namespace std;

class InputScanImg : public InputVideo {

public:
	InputScanImg(HWND hParentWnd);
	virtual ~InputScanImg();
	virtual bool SelFile();
	virtual bool LoadFile();
	virtual bool GetNextFrame(cv::Mat &frame);
	virtual bool isBegin() {
		return m_uiCurYPos == 0;
	};
	void SetTempo(int tempo);
	double GetNextFPS();
	void SetSpoolDiameter(double dia) {
		m_dOrgSpoolDiameter = m_dCurSpoolDiameter = dia;

		TCHAR strBuf[20];
		_stprintf_s(strBuf, 20, _T("%6.3f spool\n"), dia);
		OutputDebugString(strBuf);
	}

private:
	cv::Mat m_img;
	UINT m_uiCurYPos;
	UINT m_uiSkipPx;
	UINT m_uiRollLeftPos, m_uiRollRightPos;
	UINT m_udMargin;
	UINT m_uiRollWidth; 
	double m_dDPI;
	double m_dRollAbsWidth = 11.25;			// in inch
	double m_dRollThickness = 0.00334646;	// in inch
	double m_dOrgSpoolDiameter;	// in inch
	double m_dCurSpoolDiameter; // in inch
	double m_dSpoolRPS;			// round per sec
	double m_dCurSpoolPos;		// between 0.0 - 1.0 round (0 - 360 degree)

	void FindRollEdges();
	string m_strImgPath;
};
