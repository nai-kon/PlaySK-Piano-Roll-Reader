#include "stdafx.h"
#include "main.h"
#include <Shellapi.h>

using namespace std;

int APIENTRY _tWinMain(_In_ HINSTANCE hInstance,
	_In_opt_ HINSTANCE hPrevInstance,
	_In_ LPTSTR    lpCmdLine,
	_In_ int       nCmdShow)
{
	CriticalSectionMng cs; 
	UNREFERENCED_PARAMETER(hPrevInstance);
	UNREFERENCED_PARAMETER(lpCmdLine);

	LoadString(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
	LoadString(hInstance, IDC_MYREADER, szWindowClass, MAX_LOADSTRING);
	MyRegisterClass(hInstance);

	if (!InitInstance(hInstance, nCmdShow)){
		return FALSE;
	}

	HACCEL hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_MYREADER));
	hInst = hInstance;

	// main message loop
	MSG msg;
	while (GetMessage(&msg, NULL, 0, 0)){
		if (!TranslateAccelerator(msg.hwnd, hAccelTable, &msg)){
			TranslateMessage(&msg);
			DispatchMessage(&msg);
		}
	}

	return (int)msg.wParam;
}


ATOM MyRegisterClass(HINSTANCE hInstance)
{
	WNDCLASSEX wcex = { sizeof(WNDCLASSEX) };
	wcex.style = 0;
	wcex.lpfnWndProc = WndProc;
	wcex.cbClsExtra = 0;
	wcex.cbWndExtra = 0;
	wcex.hInstance = hInstance;
	wcex.hIcon = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_MYREADER));
	wcex.hCursor = LoadCursor(NULL, IDC_ARROW);
	wcex.hbrBackground = (HBRUSH)(COLOR_WINDOW);
	wcex.lpszMenuName = MAKEINTRESOURCE(IDC_MYREADER);
	wcex.lpszClassName = szWindowClass;
	wcex.hIconSm = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

	return RegisterClassEx(&wcex);
}


BOOL InitInstance(HINSTANCE hInstance, int nCmdShow)
{
	HWND hWnd = CreateWindow(szWindowClass, szTitle, WS_OVERLAPPEDWINDOW^WS_MAXIMIZEBOX^WS_THICKFRAME,
		CW_USEDEFAULT, CW_USEDEFAULT, VIDEO_WIDTH+140, VIDEO_HEIGHT+85, NULL, NULL, hInstance, NULL);

	if (!hWnd) return FALSE;

	ShowWindow(hWnd, nCmdShow);
	UpdateWindow(hWnd);
	return TRUE;
}


static int SelectPlayer(HWND &hWnd)
{
	GetTrackerFiles();
	::EnterCriticalSection(&g_csExclusiveThread);

	// Release Player instance
	if (g_hInstPlayer){
		g_hInstPlayer->NoteAllOff(g_hMidiOut);
		delete g_hInstPlayer;
		g_hInstPlayer = NULL;
	}

	// Create Player instance
	if (g_strTrackerName.find(_T("88Note")) != string::npos) {
		g_hInstPlayer = new Player();
	}
	else if (g_strTrackerName.find(_T("Duo-Art")) != string::npos) {
		g_hInstPlayer = new DuoArt();
	}
	else if (g_strTrackerName.find(_T("Ampico_A")) != string::npos) {
		g_hInstPlayer = new AmpicoA();
	}

	// Load Player Settings
	tstring configpath = _T("config\\") + g_strTrackerName + _T(".json");
	if (!g_hInstPlayer || g_hInstPlayer->LoadPlayerSettings(configpath.c_str()) != 0){
		MessageBox(hWnd, _T("Error : Player Setting File Load Failed"), _T("Error"), MB_ICONWARNING | MB_OK);
		delete g_hInstPlayer;
		g_hInstPlayer = NULL;
		DestroyWindow(hWnd);
		return -1;
	}

	// Disp Max/Min Velocity
	TCHAR szBufVelocity[10];
	wsprintf(szBufVelocity, _T("%d"), g_hInstPlayer->GetMinVelocity());
	SetWindowText(g_hStMinVelo, szBufVelocity);
	wsprintf(szBufVelocity, _T("%d"), g_hInstPlayer->GetMaxVelocity());
	SetWindowText(g_hStMaxVelo, szBufVelocity);

	::LeaveCriticalSection(&g_csExclusiveThread);
	return 0;
}


static void EnTempoSlider()
{
	EnableWindow(g_hSlFps, FALSE);
	ShowWindow(g_hSlFps, SW_HIDE);
	EnableWindow(g_hSlTempo, TRUE);
	ShowWindow(g_hSlTempo, SW_SHOW);

	g_dwSpeed = 80;
	SendMessage(g_hSlTempo, TBM_SETPOS, TRUE, g_dwSpeed);
	SetWindowText(g_hStSpeed, _T("Tempo 80"));
}

static void EnFpsSlider()
{
	EnableWindow(g_hSlTempo, FALSE);
	ShowWindow(g_hSlTempo, SW_HIDE);
	EnableWindow(g_hSlFps, TRUE);
	ShowWindow(g_hSlFps, SW_SHOW);

	g_dwSpeed = 60;
	SendMessage(g_hSlFps, TBM_SETPOS, TRUE, g_dwSpeed);
	SetWindowText(g_hStSpeed, _T("60 FPS"));
}


// Main Windows Proc
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
	static HANDLE hPlayerThread;					
	static FILE *fpAutoTracking = NULL;

	switch (message){
	case WM_CREATE:

		// Create Status Bar
		InitCommonControls();
		g_hStatusBar = CreateStatusBar(hWnd);
		CreateButton(hWnd);

		// Disp Setting Dialog
		if (DialogBox(hInst, MAKEINTRESOURCE(IDD_OPTBOX), hWnd, SettingDlgProc) == IDCANCEL){
			DestroyWindow(hWnd);
			break;
		}

		g_hdcImage = cvhelper::DoubleBuffer_Create(hWnd, VIDEO_WIDTH, VIDEO_HEIGHT);

		if (SelectPlayer(hWnd) == -1){
			break;
		}

		g_bAppEndFlag = false;
		hPlayerThread = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)PlayerThread, (LPVOID)hWnd, 0, NULL);
		SetThreadPriority(hPlayerThread, THREAD_PRIORITY_TIME_CRITICAL);
		break;

	case WM_COMMAND: {
		WORD wmId = LOWORD(wParam);
		WORD wmEvent = HIWORD(wParam);


		switch (wmId){
		case IDM_OPEN_VIDEO:
		{
			::EnterCriticalSection(&g_csExclusiveThread);
			InputVideo* tmp = new InputVideo(hWnd);
			if (tmp->SelFile()) {
				delete g_hVideoSrc;
				tmp->LoadFile();
				g_hVideoSrc = tmp;
				EnFpsSlider();
			}
			::LeaveCriticalSection(&g_csExclusiveThread);
		}
		break;
		case IDM_OPEN_SCANIMAGE:
		{
			::EnterCriticalSection(&g_csExclusiveThread);
			InputVideo* tmp = new InputScanImg(hWnd);
			if (tmp->SelFile()) {
				delete g_hVideoSrc;
 				tmp->LoadFile();
				g_hVideoSrc = tmp;
				EnTempoSlider();
			}
			::LeaveCriticalSection(&g_csExclusiveThread);
		}
		break;
		case IDM_ABOUT:
			DialogBox(hInst, MAKEINTRESOURCE(IDD_ABOUTBOX), hWnd, About);
			break;
		case IDM_OPTION:
			DlgState = SettingDlgState::DLG1ONLY;
			if (DialogBox(hInst, MAKEINTRESOURCE(IDD_OPTBOX), hWnd, SettingDlgProc) == IDOK) {
				SelectPlayer(hWnd);
			}
			break;
		case IDC_BTN_START_ENGINE:
		{
			// Play / Stop
			MENUITEMINFO menuInfo = { sizeof(MENUITEMINFO) };
			menuInfo.fMask = MIIM_STATE;
			::EnterCriticalSection(&g_csExclusiveThread);

			if (!g_bEngineStart) {
				g_bEngineStart = true;
				SetWindowText(g_hBtnStartEngine, _T("Stop"));
				menuInfo.fState = MFS_GRAYED; //disable the menuitem "OPTION"
			}
			else {
				g_bEngineStart = false;
				SetWindowText(g_hBtnStartEngine, _T("Play"));
				menuInfo.fState = MFS_ENABLED; //enable the menuitem "OPTION"
			}

			// Set MenuItems 
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPTION, FALSE, &menuInfo);
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPEN_VIDEO, FALSE, &menuInfo);
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPEN_SCANIMAGE, FALSE, &menuInfo);

			::LeaveCriticalSection(&g_csExclusiveThread);

		}
		break;
		case IDC_BTN_MIDION:
		{
			// Midi On / Off
			MENUITEMINFO menuInfo = { sizeof(MENUITEMINFO) };
			menuInfo.fMask = MIIM_STATE;
			static bool bMidiOn = false;
			::EnterCriticalSection(&g_csExclusiveThread);

			if (bMidiOn) {
				bMidiOn = false;
				g_hInstPlayer->SetEmulateOff();
				g_hInstPlayer->NoteAllOff(g_hMidiOut);
				SetWindowText(g_hBtnMidiOn, _T("Midi On"));
				menuInfo.fState = MFS_ENABLED; //enable the menuitem "OPTION"
			}
			else {
				bMidiOn = true;
				g_hInstPlayer->SetEmulateOn();
				SetWindowText(g_hBtnMidiOn, _T("Midi Off"));
				menuInfo.fState = MFS_GRAYED; //disable the menuitem "OPTION"
			}

			// Set MenuItems 
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPTION, FALSE, &menuInfo);
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPEN_VIDEO, FALSE, &menuInfo);
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPEN_SCANIMAGE, FALSE, &menuInfo);

			::LeaveCriticalSection(&g_csExclusiveThread);

		}
		break;
		case IDC_CB_AUTOTRACK:
			g_bAutoTracking = SendMessage(g_hbAutoTrack, BM_GETCHECK, 0, 0);
			break;

		case IDM_EXIT:
			SendMessage(hWnd, WM_CLOSE, NULL, NULL);
			break;

		default:
			return DefWindowProc(hWnd, message, wParam, lParam);
		}
		break;
	}
	case WM_HSCROLL:
	{
		static TCHAR szbuf[10];
		if (GetDlgItem(hWnd, IDC_SL_FPS) == (HWND)lParam) {
			g_dwSpeed = SendMessage(g_hSlFps, TBM_GETPOS, NULL, NULL);
			wsprintf(szbuf, TEXT("%2d FPS"), g_dwSpeed);
			SetWindowText(g_hStSpeed, szbuf);
		}
		else if (GetDlgItem(hWnd, IDC_SL_TEMPO) == (HWND)lParam) {
			g_dwSpeed = SendMessage(g_hSlTempo, TBM_GETPOS, NULL, NULL);
			wsprintf(szbuf, TEXT("Tempo %2d"), g_dwSpeed);
			SetWindowText(g_hStSpeed, szbuf);
		}

		break;
	}
	case WM_NOTIFY:
	{
		static TCHAR strBuf[MAX_LOADSTRING] = { 0 };
		LPNMUPDOWN lpnmud = (LPNMUPDOWN)lParam;

		switch (wParam) {
		case IDC_SPIN_TRACKING_OFFSET:
			// Tracking Offset
			if (lpnmud->hdr.code == UDN_DELTAPOS) {
				int iTrackinfOff = g_hInstPlayer->GetRollOffset();
				if (lpnmud->iDelta < 0) {
					iTrackinfOff++;
				}
				else if (lpnmud->iDelta > 0) {
					iTrackinfOff--;
				}
				g_hInstPlayer->SetRollOffset(iTrackinfOff);
				wsprintf(strBuf, _T("%s%d"), iTrackinfOff >= 0 ? "+" : "",iTrackinfOff);
				SetWindowText(g_stRollOffset, strBuf);

			}
			break;

		case IDC_SPIN_NOTEONFRAMES:
			// Note On Frames
			if (lpnmud->hdr.code == UDN_DELTAPOS) {
				int iNoteOnFrames = g_hInstPlayer->GetNoteOnFrames();
				if (lpnmud->iDelta < 0) {
					if(iNoteOnFrames < MAXNoteOnFrames) iNoteOnFrames++;
				}
				else if (lpnmud->iDelta > 0) {
					if(iNoteOnFrames > 0)iNoteOnFrames--;
				}
				g_hInstPlayer->SetNoteOnFrames(iNoteOnFrames);
				wsprintf(strBuf, TEXT("%d"), iNoteOnFrames + 1);
				SetWindowText(g_stNoteOnFrame, strBuf);
			}
			break;
		}
	}
		break;

	case WM_PAINT:
	{
		// show velocity
		static int pre_bass_vel = 0;
		static TCHAR szbuf[10];
		int bass_vel = g_hInstPlayer->GetBassVelocity();
		if (pre_bass_vel != bass_vel) {
			pre_bass_vel = bass_vel;
			wsprintf(szbuf, _T("%d"), bass_vel);
			SetWindowText(g_hStBassVelo, szbuf);
		}

		static int pre_treb_vel = 0;
		int treb_vel = g_hInstPlayer->GetTrebleVelocity();
		if (pre_treb_vel != treb_vel) {
			pre_treb_vel = treb_vel;
			wsprintf(szbuf, _T("%d"), treb_vel);
			SetWindowText(g_hStTrebleVelo, szbuf);
		}

		PAINTSTRUCT ps;
		HDC hdc = BeginPaint(hWnd, &ps);
		BitBlt(hdc, 0, 0, VIDEO_WIDTH, VIDEO_HEIGHT, g_hdcImage, 0, 0, SRCCOPY);
		EndPaint(hWnd, &ps);
	}
		break;

	case WM_SIZE:
		// Send size changed message to status bar 
		SendMessage(g_hStatusBar, message, wParam, lParam);
		break;

	case WM_CLOSE:
		g_bAppEndFlag = true;
		WaitForSingleObject(hPlayerThread, 500);
		if (CloseHandle(hPlayerThread)) DestroyWindow(hWnd);		
		break;

	case WM_DESTROY:
		delete g_hInstPlayer;
		delete g_hVideoSrc;
		if(fpAutoTracking) fclose(fpAutoTracking);
		midiOutReset(g_hMidiOut);
		midiOutClose(g_hMidiOut);
		PostQuitMessage(0);

		break;

	default:
		return DefWindowProc(hWnd, message, wParam, lParam);
	}
	return 0;
}


// About Dialog
INT_PTR CALLBACK About(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
	UNREFERENCED_PARAMETER(lParam);
	switch (message) {
	case WM_INITDIALOG:
		return (INT_PTR)TRUE;

	case WM_COMMAND:
		if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL) {
			EndDialog(hDlg, LOWORD(wParam));
			return (INT_PTR)TRUE;
		}
		break;
	case WM_NOTIFY:
		switch (((LPNMHDR)lParam)->code) {

		case NM_CLICK:
		case NM_RETURN:
			// open github link
			ShellExecute(NULL, _T("open"), ((PNMLINK)lParam)->item.szUrl, NULL, NULL, SW_SHOW);
			break;
		}
		break;
	}

	return (INT_PTR)FALSE;
}


// list config file names
vector<tstring> GetTrackerFiles()
{
	vector<tstring> vecFNames;
	WIN32_FIND_DATA fd;
	HANDLE hnd = FindFirstFile(_T("config\\*.json"), &fd);

	if (hnd != INVALID_HANDLE_VALUE) {
		do {
			if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
				continue;
			}
			tstring fname = fd.cFileName;
			if (fname.find(SETTING_JSON_NAME) != string::npos) {
				continue;
			}
			vecFNames.push_back(fname.substr(0, fname.rfind(_T(".json"))));
		} while (FindNextFile(hnd, &fd));
	}
	FindClose(hnd);

	return vecFNames;
}


// Setting Dialog Proc
BOOL CALLBACK SettingDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{

	static HWND hCmbMidioutDev;
	static HWND hCmbPlayer;
	static vector <int> vecMidiDevNo;
	static MIDIOUTCAPS cap;

	switch (message)
	{
	case WM_INITDIALOG:
	{
		// Show MidiOut Device List
		hCmbMidioutDev = GetDlgItem(hDlg, IDC_COMBO_MIDIOUT);

		int iMidiOutDevCnt = midiOutGetNumDevs();
		for (int iDevNo = 0; iDevNo < iMidiOutDevCnt; ++iDevNo){
			if (midiOutGetDevCaps(iDevNo, &cap, sizeof(cap)) != MMSYSERR_NOERROR) {
				continue; 
			}

			HMIDIOUT hDummy;
			MMRESULT midiOpen;
			if ((midiOpen = midiOutOpen(&hDummy, iDevNo, 0, 0, CALLBACK_NULL)) != MMSYSERR_NOERROR
				&& midiOpen != MMSYSERR_ALLOCATED){
				continue;	
			}

			// Add Midiout Enable Devs to Combo Box
			midiOutClose(hDummy);
			vecMidiDevNo.push_back(iDevNo);
			ComboBox_AddString(hCmbMidioutDev, cap.szPname);
		}
		ComboBox_SetCurSel(hCmbMidioutDev, 0);

		// Show Virtual Tracker File List
		hCmbPlayer = GetDlgItem(hDlg, IDC_COMBO_PLAYER);

		for (tstring fname : GetTrackerFiles()) {
			ComboBox_AddString(hCmbPlayer, fname.c_str());
		}
		ComboBox_SetCurSel(hCmbPlayer, 0);

		// Change Dlg State
		switch (DlgState) {
		case SettingDlgState::DLG1:
			EnableWindow(GetDlgItem(hDlg, IDOKDLG), FALSE);
			ShowWindow(GetDlgItem(hDlg, IDC_WEBCAM), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_VIDEOFILE), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_SCAN), SW_HIDE);
			break;

		case SettingDlgState::DLG1ONLY:
			EnableWindow(GetDlgItem(hDlg, IDOKDLG), TRUE);
			ShowWindow(GetDlgItem(hDlg, IDC_DLGNEXT), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_WEBCAM), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_VIDEOFILE), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_SCAN), SW_HIDE);
			break;
		}

	}
	return TRUE;

	case WM_COMMAND:
		switch (LOWORD(wParam)){
		case IDOKDLG:
		{
			::EnterCriticalSection(&g_csExclusiveThread);

			if (g_hMidiOut) {
				midiOutReset(g_hMidiOut);
				midiOutClose(g_hMidiOut);
			}

			// Open Midiout
			int iMidioutDevNo = vecMidiDevNo.at(ComboBox_GetCurSel(hCmbMidioutDev));
			if (midiOutOpen(&g_hMidiOut, iMidioutDevNo, 0, 0, CALLBACK_NULL) != MMSYSERR_NOERROR){
				MessageBox(hDlg, _T("Error : Midi port can't open!"), _T("Error"), MB_ICONWARNING | MB_OK);
				return TRUE;
			}

			// Show MidioutDev Name to Status Bar
			TCHAR strBuf[MAX_LOADSTRING] = { 0 };
			midiOutGetDevCaps(iMidioutDevNo, &cap, sizeof(cap));
			wsprintf(strBuf, _T("Midi Out : %s"), cap.szPname);
			SendMessage(g_hStatusBar, SB_SETTEXT, 0, (LPARAM)strBuf);

			TCHAR szBuf[MAX_PATH];
			ComboBox_GetText(hCmbPlayer, szBuf, sizeof(szBuf));
			g_strTrackerName = szBuf;

			// Show Player Name to Status Bar
			SendMessage(g_hStatusBar, SB_SETTEXT, 1, (LPARAM)g_strTrackerName.c_str());

			// select video src file
			if (DlgState == SettingDlgState::DLG1ONLY){
				EndDialog(hDlg, IDOK);
			}
			else if (g_hVideoSrc && g_hVideoSrc->SelFile() && g_hVideoSrc->LoadFile()){
				EndDialog(hDlg, IDOK);
			}

			::LeaveCriticalSection(&g_csExclusiveThread);
			return TRUE;
		}

		case IDCANCEL:
			EndDialog(hDlg, IDCANCEL);

			return TRUE;

		case IDC_DLGNEXT:
			if (DlgState == SettingDlgState::DLG1){
				
				// Transition to Inputsrc Sel Dlg
				SetWindowText(hDlg, _T("Input"));
				SetWindowText(GetDlgItem(hDlg, IDC_DLGNEXT), _T("Prev"));
				EnableWindow(GetDlgItem(hDlg, IDOKDLG), TRUE);
				ShowWindow(GetDlgItem(hDlg, IDC_COMBO_MIDIOUT), SW_HIDE);
				ShowWindow(GetDlgItem(hDlg, IDC_COMBO_PLAYER), SW_HIDE);
				ShowWindow(GetDlgItem(hDlg, IDC_STATIC1), SW_HIDE);
				ShowWindow(GetDlgItem(hDlg, IDC_STATIC2), SW_HIDE);

				ShowWindow(GetDlgItem(hDlg, IDC_WEBCAM), SW_SHOW);
				ShowWindow(GetDlgItem(hDlg, IDC_VIDEOFILE), SW_SHOW);
				ShowWindow(GetDlgItem(hDlg, IDC_SCAN), SW_SHOW);
				DlgState = SettingDlgState::DLG2;

			}
			else if (DlgState == SettingDlgState::DLG2){

				// Transition to Device Sel Dlg
				SetWindowText(hDlg, _T("Player Settting"));
				SetWindowText(GetDlgItem(hDlg, IDC_DLGNEXT), _T("Next"));
				EnableWindow(GetDlgItem(hDlg, IDOKDLG), FALSE);
				ShowWindow(GetDlgItem(hDlg, IDC_COMBO_MIDIOUT), SW_SHOW);
				ShowWindow(GetDlgItem(hDlg, IDC_COMBO_PLAYER), SW_SHOW);
				ShowWindow(GetDlgItem(hDlg, IDC_STATIC1), SW_SHOW);
				ShowWindow(GetDlgItem(hDlg, IDC_STATIC2), SW_SHOW);

				ShowWindow(GetDlgItem(hDlg, IDC_WEBCAM), SW_HIDE);
				ShowWindow(GetDlgItem(hDlg, IDC_VIDEOFILE), SW_HIDE);
				ShowWindow(GetDlgItem(hDlg, IDC_SCAN), SW_HIDE);
				DlgState = SettingDlgState::DLG1;
			}
			return TRUE;

		case IDC_WEBCAM:
			delete g_hVideoSrc;
			g_hVideoSrc = new InputWebcam(hDlg);
			EnFpsSlider();
			return TRUE;

		case IDC_VIDEOFILE:
			delete g_hVideoSrc;
			g_hVideoSrc = new InputVideo(hDlg);
			EnFpsSlider();
			return TRUE;

		case IDC_SCAN:
			delete g_hVideoSrc;
			g_hVideoSrc = new InputScanImg(hDlg);
			EnTempoSlider();
			return TRUE;

		}

	}
	return FALSE;
}


HWND CreateStatusBar(const HWND &hWnd)
{
	int sb_pos[3] = { 300, -1 };
	HWND status = CreateWindowEx(0, STATUSCLASSNAME, NULL, WS_CHILD | CCS_BOTTOM | WS_VISIBLE,
		0, 0, 0, 0, hWnd, (HMENU)MY_STATUS, hInst, NULL);

	SendMessage(status, SB_SETPARTS, 2, (LPARAM)sb_pos);
	SendMessage(status, SB_SETTEXT, 0, (LPARAM)_T("Midi Out"));
	SendMessage(status, SB_SETTEXT, 1, (LPARAM)_T("Player "));

	return status;
}


int CreateButton(const HWND &hWnd)
{	
	// Play/Stop Button
	g_hBtnStartEngine = CreateWindow(_T("BUTTON"),_T("Play"), WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 645,15, 110, 40, hWnd, (HMENU)IDC_BTN_START_ENGINE, hInst, NULL);
	SendMessage(g_hBtnStartEngine, WM_SETFONT, (WPARAM)CreateFont(22, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET, 
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE,_T("Arial")),MAKELPARAM(TRUE,0));

	// Midi On/Off Button
	g_hBtnMidiOn = CreateWindow(_T("BUTTON"), _T("Midi On"), WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 645, 65, 110, 40, hWnd, (HMENU)IDC_BTN_MIDION, hInst, NULL);
	SendMessage(g_hBtnMidiOn, WM_SETFONT, (WPARAM)CreateFont(22, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Tempo/FPS disp
	g_hStSpeed = CreateWindow(_T("STATIC"), _T(""), WS_CHILD | WS_VISIBLE, 645, 115, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStSpeed, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	
	// FPS slider
	g_hSlFps = CreateWindowEx(0, TRACKBAR_CLASS, NULL, WS_CHILD | TBS_AUTOTICKS, 645, 135, 110, 35, hWnd, (HMENU)IDC_SL_FPS, hInst, NULL);
	SendMessage(g_hSlFps, TBM_SETRANGE, TRUE, MAKELPARAM(20, 120));
	SendMessage(g_hSlFps, TBM_SETTICFREQ, 10, 0);
	SendMessage(g_hSlFps, TBM_SETPAGESIZE, 0, 5);
	SendMessage(g_hSlFps, TBM_SETPOS, TRUE, 60);

	// Tempo slider
	g_hSlTempo = CreateWindowEx(0, TRACKBAR_CLASS, NULL, WS_CHILD | TBS_AUTOTICKS, 645, 135, 110, 35, hWnd, (HMENU)IDC_SL_TEMPO, hInst, NULL);
	SendMessage(g_hSlTempo, TBM_SETRANGE, TRUE, MAKELPARAM(50, 140));
	SendMessage(g_hSlTempo, TBM_SETTICFREQ, 10, 0);
	SendMessage(g_hSlTempo, TBM_SETPAGESIZE, 0, 5);
	SendMessage(g_hSlTempo, TBM_SETPOS, TRUE, 80);

	// Max Velocity text
	HWND hTmp = CreateWindow(_T("STATIC"), _T("Max Velocity"), WS_CHILD | WS_VISIBLE, 645, 175, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(hTmp, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hStMaxVelo = CreateWindow(_T("STATIC"), _T("90"), WS_CHILD | WS_VISIBLE, 645, 190, 110, 20, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStMaxVelo, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Min Velocity text
	hTmp = CreateWindow(_T("STATIC"), _T("Min Velocity"), WS_CHILD | WS_VISIBLE, 645, 210, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(hTmp, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hStMinVelo = CreateWindow(_T("STATIC"), _T("90"), WS_CHILD | WS_VISIBLE, 645, 225, 110, 25, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStMinVelo, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Bass Velocity text
	hTmp = CreateWindow(_T("STATIC"), _T("Bass Velocity"), WS_CHILD | WS_VISIBLE, 645, 250, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(hTmp, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hStBassVelo = CreateWindow(_T("STATIC"), _T("0"), WS_CHILD | WS_VISIBLE, 645, 265, 110, 20, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStBassVelo, WM_SETFONT, (WPARAM)CreateFont(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Treble Velocity text
	hTmp = CreateWindow(_T("STATIC"), _T("Treble Velocity"), WS_CHILD | WS_VISIBLE, 645, 285, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(hTmp, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hStTrebleVelo = CreateWindow(_T("STATIC"), _T("0"), WS_CHILD | WS_VISIBLE, 645, 300, 110, 25, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStTrebleVelo, WM_SETFONT, (WPARAM)CreateFont(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Tracking Offset text
	hTmp = CreateWindow(_T("STATIC"), _T("Tracker-Bar Offset"), WS_CHILD | WS_VISIBLE, 645, 325, 110, 20, hWnd, NULL, hInst, NULL);
	SendMessage(hTmp, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	g_stRollOffset = CreateWindow(_T("STATIC"), _T("+0"), WS_CHILD | WS_VISIBLE, 645, 345, 40, 25, hWnd, NULL, hInst, NULL);
	SendMessage(g_stRollOffset, WM_SETFONT, (WPARAM)CreateFont(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Tracking Offset Slider
	CreateWindow(UPDOWN_CLASS, _T("SP_RED"), WS_CHILD | WS_VISIBLE | WS_TABSTOP | UDS_WRAP | UDS_ARROWKEYS | UDS_ALIGNRIGHT | UDS_HORZ
		| UDS_SETBUDDYINT ,685, 345, 60, 25,hWnd, (HMENU)(IDC_SPIN_TRACKING_OFFSET),hInst, NULL);

	// Auto Tracking CheckBox
	g_hbAutoTrack = CreateWindow(TEXT("BUTTON"), TEXT("Auto Tracking"), WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX, 645, 370, 100, 20, hWnd, (HMENU)IDC_CB_AUTOTRACK, hInst, NULL);
	SendMessage(g_hbAutoTrack, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	SendMessage(g_hbAutoTrack, BM_SETCHECK, BST_CHECKED, 0);

	// Note-On Frame text
	hTmp = CreateWindow(_T("STATIC"), _T("Note-On Frames"), WS_CHILD | WS_VISIBLE, 645, 400, 110, 20, hWnd, NULL, hInst, NULL);
	SendMessage(hTmp, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	
	g_stNoteOnFrame = CreateWindow(_T("STATIC"), _T("1"), WS_CHILD | WS_VISIBLE, 645, 420, 40, 25, hWnd, NULL, hInst, NULL);
	SendMessage(g_stNoteOnFrame, WM_SETFONT, (WPARAM)CreateFont(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Note-on Frame Slider
	CreateWindow(UPDOWN_CLASS, _T("SP_RED"), WS_CHILD | WS_VISIBLE | WS_TABSTOP | UDS_WRAP | UDS_ARROWKEYS | UDS_ALIGNRIGHT | UDS_HORZ
		| UDS_SETBUDDYINT, 685, 420, 60, 25, hWnd, (HMENU)(IDC_SPIN_NOTEONFRAMES), hInst, NULL);


	return 0;
}


static void WaitForNextFrame(double fps)
{

	LARGE_INTEGER nCurFrameTime;
	static LARGE_INTEGER nLastFrameTime = { 0 };

	static LARGE_INTEGER nFreq = {0};
	if (nFreq.LowPart == 0 && nFreq.HighPart == 0)
		QueryPerformanceFrequency(&nFreq);
	
	double dPassTime = 0;
	double msecPerFrame = 1000.0 / fps;
	do {
		// high precision wait
		QueryPerformanceCounter(&nCurFrameTime);
		dPassTime = (nCurFrameTime.QuadPart - nLastFrameTime.QuadPart) * 1000.0 / (double)nFreq.QuadPart;
	} while (msecPerFrame > dPassTime);

	nLastFrameTime = nCurFrameTime;

	TCHAR strBuf[20];
	_stprintf_s(strBuf, 20, _T("%6.3f fps\n"), 1000.0 / dPassTime);
	OutputDebugString(strBuf);

	return;
}


DWORD WINAPI PlayerThread(LPVOID lpdata)
{
	timeBeginPeriod(1);

	while (!g_bAppEndFlag){

		::EnterCriticalSection(&g_csExclusiveThread);

		if (g_hVideoSrc->isBegin()) {
			g_hVideoSrc->SetSpoolDiameter(g_hInstPlayer->GetSpoolDiameter());
		}

		static int pre_tempo = 0;
		if (g_dwSpeed != pre_tempo || g_hVideoSrc->isBegin()) {
			pre_tempo = g_dwSpeed;
			g_hVideoSrc->SetTempo(pre_tempo);
		}

		// show beginning frame
		double dRequiredFps = 60;
		if (g_bEngineStart || g_hVideoSrc->isBegin()){
			// roll acceleration by increse frame rate
			dRequiredFps = g_hVideoSrc->GetNextFPS();

			cv::Mat frame;
			if (g_hVideoSrc->GetNextFrame(frame)) {
				// AutoTracking 
				static int pre_offset = 0;
				int cur_offset = g_hInstPlayer->GetTrackerOffset(frame);
				if (g_bAutoTracking && pre_offset != cur_offset) {
					pre_offset = cur_offset;
					g_hInstPlayer->SetRollOffset(cur_offset);
					TCHAR bufStr[MAX_LOADSTRING] = { 0 };
					wsprintf(bufStr, _T("%s%d"), cur_offset >= 0 ? "+" : "", cur_offset);
					SetWindowText(g_stRollOffset, bufStr);
				}

				WaitForNextFrame(dRequiredFps);

				// Emulates Roll Image to Midi Siganl
				g_hInstPlayer->SetFrameRate((int)dRequiredFps);
				g_hInstPlayer->Emulate(frame, g_hMidiOut);
				cvhelper::cvtMat2HDC()(g_hdcImage, frame);
			}

			static RECT rcClipping = { 0, 0, VIDEO_WIDTH, VIDEO_HEIGHT };
			InvalidateRect((HWND)lpdata, &rcClipping, FALSE);
		
		}
		::LeaveCriticalSection(&g_csExclusiveThread);
		Sleep(3);
	}

	timeEndPeriod(1);

	return 0;
}
