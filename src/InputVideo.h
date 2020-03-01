#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>

using namespace std;

class InputVideo{

public:
	InputVideo() {};
	virtual ~InputVideo();
	virtual bool SelSrcFile(const HWND &hParentWnd);
	virtual bool GetNextFrame(cv::Mat &frame);
	virtual bool isBegin() {
		// first 5 frames as begin
		return (UINT)m_cap.get(CV_CAP_PROP_POS_FRAMES) < 5;
	};

	int GetTrackingOffset() {
		return m_iTrackingOffset;
	};


protected:
	int m_iTrackingOffset = 0;

private:
	cv::VideoCapture m_cap;
	map<UINT, INT> m_mapTrackingOffset;

	void LoadTrackingOffset(map<UINT, INT> &mapVal);
};
