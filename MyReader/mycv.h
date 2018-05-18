#pragma once

#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>

namespace mycv{

	struct cvtMat2HDC {

	private:
		static BITMAPINFO hinfo;
		HBITMAP hbmp;
		HDC hdc2;

	public:
		bool operator() (HDC hdc, const cv::Mat image);
	};

	class MngVideoCapture{

	private:
		cv::VideoCapture vc;
		cv::Mat frame;
		const int fw, fh;
		HBITMAP hbmp;
		HDC hdc2;

	public:
		MngVideoCapture(const int DevideID) : vc(DevideID),
			fw(static_cast<int>(vc.get(CV_CAP_PROP_FRAME_WIDTH))),
			fh(static_cast<int>(vc.get(CV_CAP_PROP_FRAME_HEIGHT))){};

		~MngVideoCapture(){};
		int GetFrameWidth()  const { return fw; };
		int GetFrameHeight() const { return fh; };
		void GetFrame() { vc >> frame;};
		double GetCapInfo(int propID) { return vc.get(propID); };
		bool  SetCapInfo(int propID, double val) { return vc.set(propID, val); };

		MngVideoCapture& operator >> (cv::Mat& image) {
			image = frame;
			return *this;
		}
		bool isDevideOpened() const { return vc.isOpened(); };

		void WriteFrame2DC(HDC hdc) const{
			cvtMat2HDC()(hdc, frame);
		};
	};

	HDC DoubleBuffer_Create(HWND hwnd, int xSize, int ySize);
}



