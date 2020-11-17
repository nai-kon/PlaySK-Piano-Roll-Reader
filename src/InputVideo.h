#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>

using namespace std;

class InputVideo{

public:
	InputVideo(HWND hParentWnd): m_hParentWnd(hParentWnd){};
	virtual ~InputVideo();
	virtual bool SelFile();
	virtual bool LoadFile();
	virtual bool GetNextFrame(cv::Mat &frame);
	virtual bool isBegin() {
		// first 5 frames as begin
		return (UINT)m_cap.get(CV_CAP_PROP_POS_FRAMES) < 5;
	};

	int GetTrackingOffset() {
		return m_iTrackingOffset;
	};
	virtual void SetSpoolDiameter(double dia) {
		// do nothing
	};
	virtual void SetTempo(int tempo) {
		m_dFps = tempo;
	};
	virtual double GetNextFPS() {
		return m_dFps;
	};

protected:
	int m_iTrackingOffset = 0;
	double m_dFps = 0.0;
	const HWND m_hParentWnd;

private:
	cv::VideoCapture m_cap;
	map<UINT, INT> m_mapTrackingOffset;
	string m_strVideoPath;
};
