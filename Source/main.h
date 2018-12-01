#pragma once

#include "resource.h"

#include "stdafx.h"
#include "Player.h"
#include "AmpicoA.h"
#include "DuoArt.h"


#pragma comment (lib, "winmm.lib")
#pragma comment(lib, "ComCtl32.lib")

// for Windows Vista,7 visual style API
#pragma comment(linker,"/manifestdependency:\"type='win32' \
  name='Microsoft.Windows.Common-Controls' \
  version='6.0.0.0' \
  processorArchitecture='x86' \
  publicKeyToken='6595b64144ccf1df' \
  language='*'\"")


#define MAX_LOADSTRING	100
#define MAX_g_dwVideoFrameRate			100
#define SETTING_INI_NAME	_T("CommonSetting.ini")

// Global Func
ATOM				MyRegisterClass(HINSTANCE hInstance);
BOOL				InitInstance(HINSTANCE, int);
LRESULT CALLBACK	WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK	About(HWND, UINT, WPARAM, LPARAM);
BOOL CALLBACK SettingDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam);
HWND CreateStatusBar(const HWND &hWnd);
int CreateButton(const HWND &hWnd);
int OpenVideoFile(const HWND &hWnd); 
int OpenWebcam(const HWND &hWnd);
DWORD WINAPI PlayerThread(LPVOID);

enum VideoSource	{ WEBCAM, VIDEOFILE };				// Input Video Source
static VideoSource g_videoSrc = VIDEOFILE;
enum SettingDlgState{ DLG1, DLG2, DLG1ONLY, DLG2ONLY };	// Kind of Setting DLG
enum VRPlayer	{ _88NOTE, _DUO_ART, _AMPICO_A };		// Kind of Virutal Tracker Bar
static LPCTSTR VRPlayerName[] = { _T("88-Note"), _T("Duo-Art"), _T("Ampico A"), NULL };

// Global Variable
HINSTANCE hInst;
TCHAR szTitle[MAX_LOADSTRING];
TCHAR szWindowClass[MAX_LOADSTRING];

static bool g_bAppEndFlag = false;
static SettingDlgState DlgState = SettingDlgState::DLG1;

// Control Handles
HWND g_hBtnStartEngine, g_hBtnMidiOn, g_hSlFrameRate;
HWND g_hStMaxVelo, g_hStMinVelo, g_hStBassVelo, g_hStTrebleVelo, g_stRollOffset, g_stNoteOnFrame;
VRPlayer g_VRPlayer = _88NOTE;
HDC g_hdcImage;									// Image from Video Frame
Player *g_hInstPlayer = NULL;					// Player Instance
HWND g_hStatusBar;								// Status Bar Handle
HMIDIOUT g_hMidiOut;							// Midiout Handle
cv::VideoCapture g_CvCap;						// OpenCV Video Capture Class
bool g_bIsTrackingSetMode = false;				// Tracking Offset Set Mode
CRITICAL_SECTION g_csExclusiveThread;			// Player Thread Exclusive by Cretical Section
bool g_bEngineStart = false;					// State of Emulates Start/Stop
DWORD g_dwVideoFrameRate = 60;					// Video FrameRate
std::string g_strVideoPath;						// Video File Path


class CriticalSectionMng{

public:
	CriticalSectionMng(){
		::InitializeCriticalSection(&g_csExclusiveThread);
	}

	~CriticalSectionMng(){
		::DeleteCriticalSection(&g_csExclusiveThread);
	}

};