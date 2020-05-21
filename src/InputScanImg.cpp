
#include "stdafx.h"
#include "InputScanImg.h"
#include <opencv2/imgproc/imgproc.hpp>
#define _USE_MATH_DEFINES
#include <math.h>

typedef basic_string<_TCHAR> tstring;
InputScanImg::InputScanImg()
{
	m_iTrackingOffset = 0;
	m_uiCurYPos = 0;
	m_uiSkipPxs = 1;
	m_uiRollLeftPos = 0;
	m_uiRollRightPos = 0;
	m_udMargin = 0;
	m_dDPI = 0;
	m_dSpoolRPS = 0;
	m_dCurSpoolDiameter = m_dOrgSpoolDiameter = 2.72; // Ampico B
	//m_dCurSpoolDiameter = m_dOrgSpoolDiameter = 1.8; // Ampico A
	m_dCurSpoolPos = 0;
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
	m_dDPI = m_uiRollWidth / m_dRollAbsWidth;
	m_dCurSpoolDiameter = m_dOrgSpoolDiameter;
	m_dCurSpoolPos = 0;
	
	// 640x480 video has 5px of margin on roll edge, so how about with scanned image?
	m_udMargin = (5.0 * m_uiRollWidth) / (VIDEO_WIDTH - 10.0);

	return true;
}



bool InputScanImg::GetNextFrame(cv::Mat &frame)
{
	int cropx = m_uiRollLeftPos - m_udMargin;
	int cropw = m_uiRollWidth + 2.0 * m_udMargin;
	int croph = (VIDEO_HEIGHT * cropw / VIDEO_WIDTH);
	int cropy = m_img.rows - croph - m_uiCurYPos;
	
	if (cropy < 0) {
		return false;
	}

	// crop to rect
	cv::Rect roi(cropx, cropy, cropw, croph);
	cv::resize(m_img(roi), frame, cv::Size(VIDEO_WIDTH, VIDEO_HEIGHT));
	m_uiCurYPos += m_uiSkipPxs;

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


// Call this function on every frame
double InputScanImg::GetNextFPS(double curFPS)
{
	if (curFPS == 0) {
		return curFPS;
	}

	// update take-up spool turn
	double dSpoolRPF = m_dSpoolRPS / curFPS;
	m_dCurSpoolPos += dSpoolRPF;

	// spool diameter will increase per one turn, this causes acceleration
	if (m_dCurSpoolPos > 1.0) {
		m_dCurSpoolPos -= 1.0;
		m_dCurSpoolDiameter += m_dRollThickness;
	}

	// how many pixels take-up per on one second
	double dTakeupPx = m_dSpoolRPS * m_dCurSpoolDiameter * M_PI * m_dDPI;

	// how many fps needed for take upping
	double next_fps = dTakeupPx / m_uiSkipPxs;
	if (next_fps == 0) {
		next_fps = 1;
	}
	return next_fps;
}


void InputScanImg::SetTempo(int tempo)
{	
	// get take-up spool rps
	m_dSpoolRPS = (tempo * 1.2) / (m_dOrgSpoolDiameter * M_PI * 60);

	// roll acceleration is done by fps change.
	double takeup_px_per_sec = (tempo * 1.2 * m_dDPI) / 60;
	for (int i = 1; i < 20; i++) {
		// search amount of skipping pixels by less than 90 fps
		if ((takeup_px_per_sec / i) < 90.0) {
			m_uiSkipPxs = i;
			break;
		}
	}
}

