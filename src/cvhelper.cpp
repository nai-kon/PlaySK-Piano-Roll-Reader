#include"stdafx.h"
#include "cvhelper.h"

bool cvhelper::cvtMat2HDC::operator() (HDC hdc, const cv::Mat image)
{
	cv::Mat _image;
	cv::flip(image, _image, 0);	// upset

	const int x = _image.cols;
	const int y = _image.rows;
	hinfo.bmiHeader.biWidth = x;
	hinfo.bmiHeader.biHeight = y;
	hinfo.bmiHeader.biBitCount = _image.channels() * 8;

	hbmp = CreateCompatibleBitmap(hdc, x, y);
	SetDIBits(hdc, hbmp, 0, y, _image.data, &hinfo, DIB_RGB_COLORS);
	hdc2 = CreateCompatibleDC(hdc);
	SelectObject(hdc2, hbmp);
	BitBlt(hdc, 0, 0, x, y, hdc2, 0, 0, SRCCOPY);
	DeleteDC(hdc2);
	DeleteObject(hbmp);

	return true;
};

BITMAPINFO cvhelper::cvtMat2HDC::hinfo = { sizeof(BITMAPINFOHEADER), VIDEO_WIDTH, VIDEO_HEIGHT, 1, 24, BI_RGB, 0, 0, 0, 0, 0, { NULL, NULL, NULL } };

HDC cvhelper::DoubleBuffer_Create(HWND hwnd, int xSize, int ySize)
{
	HDC hdc;
	static HDC bhdc;
	static HBITMAP hBackBMP;
	hdc = GetDC(hwnd);
	bhdc = CreateCompatibleDC(hdc);
	hBackBMP = CreateCompatibleBitmap(hdc, xSize, ySize);	
	SelectObject(bhdc, hBackBMP);			
	PatBlt(bhdc, 0, 0, xSize, ySize, BLACKNESS);		
	DeleteObject(hBackBMP);				
	ReleaseDC(hwnd, hdc);

	return bhdc;
}