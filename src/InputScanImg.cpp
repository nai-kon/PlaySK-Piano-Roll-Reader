
#include "stdafx.h"
#include "InputScanImg.h"
#include <opencv2/imgproc/imgproc.hpp>

typedef basic_string<_TCHAR> tstring;
InputScanImg::InputScanImg()
{
	m_iTrackingOffset = 0;
	m_dCurYPos = 0;
	m_uiRollLeftPos = 0;
	m_uiRollRightPos = 0;
	m_uiMargin = 0;
}


InputScanImg::~InputScanImg()
{
}

bool InputScanImg::SelSrcFile(const HWND &hParentWnd)
{
	// open scanned roll image 
	TCHAR szFilePath[MAX_PATH] = { 0 };
	OPENFILENAME ofn = { sizeof(ofn) };
	ofn.hwndOwner = hParentWnd;
	ofn.lpstrFilter = _T("Scanned Image(jpg, png, tiff)\0*.jpg;*.png;*.tiff\0");
	ofn.lpstrFile = szFilePath;
	ofn.nMaxFile = MAX_PATH;
	ofn.nMaxFileTitle = MAX_PATH;
	ofn.Flags = OFN_FILEMUSTEXIST | OFN_NOCHANGEDIR;
	ofn.lpstrTitle = _T("Open Scanned Piano Roll Image");
	if (!GetOpenFileName(&ofn)) {
		return false;
	}

	string strImgPath;
	size_t size(0);
	char buffer[2 * MAX_PATH + 2] = { 0 };
	setlocale(LC_CTYPE, "Japanese_Japan.932");
	wcstombs_s(&size, buffer, MAX_PATH, szFilePath, MAX_PATH);
	strImgPath.assign(buffer);

	HCURSOR pre = SetCursor(LoadCursor(NULL, IDC_WAIT));  // wait cursor
	m_img = cv::imread(strImgPath);
	SetCursor(pre);
	if (!m_img.data) {
		MessageBox(hParentWnd, _T("Failed to Load Image"), _T("Error"), MB_OK | MB_ICONWARNING);
		return false;
	}

	FindRollEdges();
	m_uiRollWidth = m_uiRollRightPos - m_uiRollLeftPos + 1;
	// 640x480 video has 5px of margin on roll edge, so how about with scanned image?
	m_uiMargin = (5 * m_uiRollWidth) / (VIDEO_WIDTH - 10);

	return true;
}



bool InputScanImg::GetNextFrame(cv::Mat &frame)
{
	int cropx = m_uiRollLeftPos - m_uiMargin;
	int cropw = m_uiRollWidth + 2 * m_uiMargin;
	int croph = (VIDEO_HEIGHT * cropw / VIDEO_WIDTH);
	int cropy = m_img.rows - croph - (int)m_dCurYPos;
	
	if (cropy < 0) {
		return false;
	}

	// crop to rect
	cv::Rect roi(cropx, cropy, cropw, croph);
	cv::resize(m_img(roi), frame, cv::Size(VIDEO_WIDTH, VIDEO_HEIGHT));
	m_dCurYPos += 2;

	return true;
}


void InputScanImg::FindRollEdges()
{
	// measure at half place of the roll
	int th = 200;
	int yoffset = (int)(m_img.rows / 2) * m_img.cols * 3;

	// find roll left edge
	for (int x = 0; x < m_img.cols / 2; x++) {
		if (m_img.data[yoffset + 3 * x] < th) {
			m_uiRollLeftPos = x;
			break;
		}
	}

	// find roll right edge
	for (int x = m_img.cols - 1; x > m_img.cols / 2; x--) {
		if (m_img.data[yoffset + 3 * x] < th) {
			m_uiRollRightPos = x;
			break;
		}
	}
}