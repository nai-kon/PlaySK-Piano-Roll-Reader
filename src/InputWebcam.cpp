
#include "stdafx.h"
#include "InputWebcam.h"
#include "json11.hpp"

InputWebcam::InputWebcam()
{
	m_iTrackingOffset = 0;
}

InputWebcam::~InputWebcam()
{
}


bool InputWebcam::SelSrcFile(const HWND &hParentWnd)
{
	// Load Webcam Device Number
	std::ifstream ifs(SETTING_JSON_NAME);
	std::string err, strjson((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
	json11::Json json = json11::Json::parse(strjson, err);
	int iWebcam_Devno = json["device"]["webcam_devno"].int_value();
	
	// Open Webcam
	if (!m_cap.open(iWebcam_Devno)) {
		MessageBox(hParentWnd, _T("Failed to Open Webcam"), _T("Error"), MB_OK | MB_ICONWARNING);
		return false;
	}
	
	return true;
}



bool InputWebcam::GetNextFrame(cv::Mat &frame)
{
	return (m_cap.grab() && m_cap.retrieve(frame));
}