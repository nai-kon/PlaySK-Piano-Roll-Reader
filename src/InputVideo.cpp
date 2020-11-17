
#include "stdafx.h"
#include "InputVideo.h"



InputVideo::~InputVideo()
{

}


bool InputVideo::SelFile()
{	
	// open video 
	TCHAR szFilePath[MAX_PATH] = { 0 };
	OPENFILENAME ofn = { sizeof(ofn) };
	ofn.hwndOwner = m_hParentWnd;
	ofn.lpstrFilter = _T("Video File(mp4, AVI)\0*.mp4;*.avi\0");
	ofn.lpstrFile = szFilePath;
	ofn.nMaxFile = MAX_PATH;
	ofn.nMaxFileTitle = MAX_PATH;
	ofn.Flags = OFN_FILEMUSTEXIST | OFN_NOCHANGEDIR;
	ofn.lpstrTitle = _T("Open Piano Roll Video File");
	if (!GetOpenFileName(&ofn)) {
		return false;
	}

	size_t size(0);
	char buffer[2 * MAX_PATH + 2] = { 0 };
	setlocale(LC_CTYPE, "Japanese_Japan.932");
	wcstombs_s(&size, buffer, MAX_PATH, szFilePath, MAX_PATH);
	m_strVideoPath.assign(buffer);

	// check video resolution
	cv::VideoCapture cap(m_strVideoPath);
	if ((cap.get(CV_CAP_PROP_FRAME_WIDTH) != VIDEO_WIDTH) || (cap.get(CV_CAP_PROP_FRAME_HEIGHT) != VIDEO_HEIGHT)) {
		MessageBox(m_hParentWnd, _T("Video Resultion is not 640x480"), _T("Error"), MB_OK | MB_ICONWARNING);
		m_strVideoPath.clear();
		return false;
	}

	return true;
}


bool InputVideo::LoadFile()
{
	m_cap.open(m_strVideoPath);

	// load auto tracking file
	m_iTrackingOffset = 0;
	m_mapTrackingOffset.clear();
	string strTrackingPath = m_strVideoPath.substr(0, m_strVideoPath.find_last_of(".")) + "_Tracking.txt";
	FILE *fp = NULL;
	fopen_s(&fp, strTrackingPath.c_str(), "r");
	if (fp) {
		UINT uiFrames = 0;
		INT iOffset = 0;
		while (fscanf_s(fp, "%u : %d", &uiFrames, &iOffset) != EOF) {
			m_mapTrackingOffset.insert(make_pair(uiFrames, iOffset));
		}
		fclose(fp);
	}

	return true;
}


bool InputVideo::GetNextFrame(cv::Mat &frame)
{
	if (m_cap.grab() && m_cap.retrieve(frame)) {

		UINT iCurFrame = (UINT)m_cap.get(CV_CAP_PROP_POS_FRAMES);
		// get tracking offset
		if (m_mapTrackingOffset.find(iCurFrame) != m_mapTrackingOffset.end()) {
			m_iTrackingOffset = m_mapTrackingOffset.at(iCurFrame);
		}

		return true;
	}

	return false;
}