
#include "stdafx.h"
#include "InputScanImg.h"
#include <opencv2/imgproc/imgproc.hpp>
#define _USE_MATH_DEFINES
#include <math.h>
#include <vector>
#include <algorithm>

typedef basic_string<_TCHAR> tstring;
InputScanImg::InputScanImg(HWND hParentWnd) : InputVideo(hParentWnd)
{
	m_iTrackingOffset = 0;
	m_uiCurYPos = 0;
	m_uiSkipPx = 1;
	m_uiRollLeftPos = 0;
	m_uiRollRightPos = 0;
	m_udMargin = 0;
	m_dDPI = 0;
	m_dSpoolRPS = 0;
	m_dCurSpoolDiameter = m_dOrgSpoolDiameter = 0.0;
	m_dCurSpoolPos = 0;
}


InputScanImg::~InputScanImg()
{
}

bool InputScanImg::SelFile()
{
	// open scanned roll image 
	TCHAR szFilePath[MAX_PATH] = { 0 };
	OPENFILENAME ofn = { sizeof(ofn) };
	ofn.hwndOwner = m_hParentWnd;
	ofn.lpstrFilter = _T("Scanned Image(jpg, png, tiff)\0*.jpg;*.png;*.tiff\0");
	ofn.lpstrFile = szFilePath;
	ofn.nMaxFile = MAX_PATH;
	ofn.nMaxFileTitle = MAX_PATH;
	ofn.Flags = OFN_FILEMUSTEXIST | OFN_NOCHANGEDIR;
	ofn.lpstrTitle = _T("Open Scanned Piano Roll Image");
	if (!GetOpenFileName(&ofn)) {
		return false;
	}

	size_t size(0);
	char buffer[2 * MAX_PATH + 2] = { 0 };
	setlocale(LC_CTYPE, "Japanese_Japan.932");
	wcstombs_s(&size, buffer, MAX_PATH, szFilePath, MAX_PATH);
	m_strImgPath.assign(buffer);

	return true;
}


bool InputScanImg::LoadFile()
{
	HCURSOR pre = SetCursor(LoadCursor(NULL, IDC_WAIT));  // wait cursor
	try{
		m_img = cv::imread(m_strImgPath);
	}
	catch (const cv::Exception& e) {
		m_img.release();
	}
	SetCursor(pre);
	if (!m_img.data) {
		MessageBox(m_hParentWnd, _T("Failed to Load Image"), _T("Error"), MB_OK | MB_ICONWARNING);
		return false;
	}

	FindRollEdges();
	m_uiRollWidth = m_uiRollRightPos - m_uiRollLeftPos + 1;
	m_dDPI = m_uiRollWidth / m_dRollAbsWidth;
	m_dCurSpoolDiameter = m_dOrgSpoolDiameter;
	m_dCurSpoolPos = 0;

	// 640x480 video has 5px of margin on roll edge, so how about with scanned image?
	m_udMargin = (5.0 * m_uiRollWidth) / (VIDEO_WIDTH - 10.0);
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
	m_uiCurYPos += m_uiSkipPx;

	return true;
}


void InputScanImg::FindRollEdges()
{
	int th = 220;

	// measure roll edges at 9 point
	vector<pair<int, int>> vRollEdges;
	for (int i = 1; i < 10; i++) {
		UINT yoffset = (UINT)(m_img.rows * i / 10.0) * m_img.cols * 3;

		// find roll left edge		
		int iRollLeftPos = 0;
		for (int x = 0; x < m_img.cols / 2; x++) {
			if (m_img.data[yoffset + 3 * x] < th) {
				iRollLeftPos = x;
				break;
			}
		}

		// find roll right edge
		int iRollRightPos = 0;
		for (int x = m_img.cols - 1; x > m_img.cols / 2; x--) {
			if (m_img.data[yoffset + 3 * x] < th) {
				iRollRightPos = x;
				break;
			}
		}

		vRollEdges.push_back(pair<int, int>(iRollLeftPos, iRollRightPos));
	}

	// sort by width, and get middle points
	sort(vRollEdges.begin(), vRollEdges.end(), [](auto const& x, auto const& y){return x.second - x.first > y.second - y.first; });
	int mid_idx = vRollEdges.size() / 2;
	m_uiRollLeftPos = vRollEdges[mid_idx].first;
	m_uiRollRightPos = vRollEdges[mid_idx].second;
}


// Call this function on every frame
double InputScanImg::GetNextFPS()
{
	static double cur_fps = 60.0;

	// update take-up spool turn
	double dSpoolRPF = m_dSpoolRPS / cur_fps;
	m_dCurSpoolPos += dSpoolRPF;

	// spool diameter will increase per one turn, this causes acceleration
	if (m_dCurSpoolPos > 1.0) {
		m_dCurSpoolPos -= 1.0;
		m_dCurSpoolDiameter += m_dRollThickness;
	}

	// how many pixels take-up per on one second
	double dTakeupPx = m_dSpoolRPS * m_dCurSpoolDiameter * M_PI * m_dDPI;

	// how many fps needed for take up
	cur_fps = dTakeupPx / m_uiSkipPx;
	
	return cur_fps;
}


void InputScanImg::SetTempo(int tempo)
{	
	// get take-up spool rps
	m_dSpoolRPS = (tempo * 1.2) / (m_dOrgSpoolDiameter * M_PI * 60);

	// roll acceleration is done by fps change.
	double takeup_px_per_sec = (tempo * 1.2 * m_dDPI) / 60;
	for (int i = 1; i < 20; i++) {
		// search amount of skipping pixels by less than 100 fps
		if ((takeup_px_per_sec / i) < 100.0) {
			m_uiSkipPx = i;
			break;
		}
	}
}

