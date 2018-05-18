#include "stdafx.h"
#include "MyReader.h"



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

	// Start App with Shift key, tracking offset write mode is enabled
	if (GetKeyState(VK_SHIFT) < 0) {
		MessageBox(GetDesktopWindow(), _T("Tracking Offset WriteMode Enabled"), szTitle, MB_OK);
		g_bIsTrackingSetMode = true;
	}

	if (!InitInstance(hInstance, nCmdShow)){
		return FALSE;
	}

	HACCEL hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_MYREADER));

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
	wcex.style = CS_HREDRAW | CS_VREDRAW;
	wcex.lpfnWndProc = WndProc;
	wcex.cbClsExtra = 0;
	wcex.cbWndExtra = 0;
	wcex.hInstance = hInstance;
	wcex.hIcon = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_MYREADER));
	wcex.hCursor = LoadCursor(NULL, IDC_ARROW);
	wcex.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
	wcex.lpszMenuName = MAKEINTRESOURCE(IDC_MYREADER);
	wcex.lpszClassName = szWindowClass;
	wcex.hIconSm = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

	return RegisterClassEx(&wcex);
}


BOOL InitInstance(HINSTANCE hInstance, int nCmdShow)
{
	hInst = hInstance;

	// Maxmize Window
	HWND hWnd = CreateWindow(szWindowClass, szTitle, WS_OVERLAPPEDWINDOW^WS_MAXIMIZEBOX^WS_THICKFRAME,
		CW_USEDEFAULT, 0, VIDEO_WIDTH+140, VIDEO_HEIGHT+85, NULL, NULL, hInstance, NULL);

	if (!hWnd) return FALSE;

	ShowWindow(hWnd, nCmdShow);
	UpdateWindow(hWnd);
	return TRUE;
}


int SelectPlayer(HWND &hWnd){

	::EnterCriticalSection(&g_csExclusiveThread);

	// Release Player instance
	if (g_hInstPlayer){
		g_hInstPlayer->NoteAllOff(g_hMidiOut);
		delete g_hInstPlayer;
		g_hInstPlayer = NULL;
	}

	// Create Player instance
	switch (g_VRPlayer) {
	case VRPlayer::_88NOTE:
		g_hInstPlayer = new Player();
		break;
	case VRPlayer::_DUO_ART:
		g_hInstPlayer = new DuoArt();
		break;
	case VRPlayer::_AMPICO_A:
		g_hInstPlayer = new AmpicoA();
		break;
	default:
		break;
	}

	// Load Player Settings
	if (g_hInstPlayer->LoadPlayerSettings() != 0){
		MessageBox(hWnd, _T("Error : Setting File Load Failed"), _T("Error"), MB_ICONWARNING | MB_OK);
		if(g_hInstPlayer) delete g_hInstPlayer;
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

		if (!g_CvCap.isOpened()) {
			MessageBox(hWnd, _T("Error : Input Source not found! program exit"), _T("Error"), MB_ICONWARNING | MB_OK);
			DestroyWindow(hWnd);
			break;
		}

		if(g_bIsTrackingSetMode){
			std::string strTrackingFile = g_strVideoPath.substr(0, g_strVideoPath.find_last_of(".")) + "_Tracking.txt";
			fopen_s(&fpAutoTracking, strTrackingFile.c_str(), "w");
		}

		g_hdcImage = mycv::DoubleBuffer_Create(hWnd, VIDEO_WIDTH, VIDEO_HEIGHT);

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

		switch (wmId)
		{
		case IDM_FILE:
			::EnterCriticalSection(&g_csExclusiveThread);
			OpenVideoFile(hWnd);
			::LeaveCriticalSection(&g_csExclusiveThread);
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
		case IDM_OPTION2:
			DlgState = SettingDlgState::DLG2ONLY;
			if (DialogBox(hInst, MAKEINTRESOURCE(IDD_OPTBOX), hWnd, SettingDlgProc) == IDOK) {
				g_hInstPlayer->NoteAllOff(g_hMidiOut);
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
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPTION2, FALSE, &menuInfo);
			SetMenuItemInfo(GetMenu(hWnd), IDM_FILE, FALSE, &menuInfo);

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

			if (!bMidiOn) {
				bMidiOn = true;
				g_hInstPlayer->SetEmulateOn();
				SetWindowText(g_hBtnMidiOn, _T("Midi Off"));
				menuInfo.fState = MFS_GRAYED; //disable the menuitem "OPTION"
			}
			else {
				bMidiOn = false;
				g_hInstPlayer->SetEmulateOff();
				g_hInstPlayer->NoteAllOff(g_hMidiOut);
				SetWindowText(g_hBtnMidiOn, _T("Midi On"));
				menuInfo.fState = MFS_ENABLED; //enable the menuitem "OPTION"
			}

			// Set MenuItems 
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPTION, FALSE, &menuInfo);
			SetMenuItemInfo(GetMenu(hWnd), IDM_OPTION2, FALSE, &menuInfo);
			SetMenuItemInfo(GetMenu(hWnd), IDM_FILE, FALSE, &menuInfo);

			::LeaveCriticalSection(&g_csExclusiveThread);

		}
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

		if (GetDlgItem(hWnd, IDC_SLIDER1) == (HWND)lParam){
			g_dwVideoFrameRate = SendMessage(g_hSlFrameRate, TBM_GETPOS, NULL, NULL);
		}
		break;

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
				wsprintf(strBuf, _T("%d"), iTrackinfOff);
				SetWindowText(g_stRollOffset, strBuf);

				// Write Tracking Offset to File
				if (g_bIsTrackingSetMode && fpAutoTracking) {
					fprintf_s(fpAutoTracking, "%u : %d\n", (UINT)g_CvCap.get(CV_CAP_PROP_POS_FRAMES), iTrackinfOff);
				}
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
		// Disp Velocity
		static int iDispCnt = 0;
		if (++iDispCnt % 2 == 0){
			iDispCnt = 0;
			TCHAR szBufVelocity[10];
			wsprintf(szBufVelocity, _T("%d"), g_hInstPlayer->GetBassVelocity());
			SetWindowText(g_hStBassVelo, szBufVelocity);
			wsprintf(szBufVelocity, _T("%d"), g_hInstPlayer->GetTrebleVelocity());
			SetWindowText(g_hStTrebleVelo, szBufVelocity);
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
		if (MessageBox(hWnd, _T("Are you sure you want to quit?"), szTitle, MB_YESNO|MB_ICONQUESTION) == IDYES){
			g_bAppEndFlag = true;
			WaitForSingleObject(hPlayerThread, 500);
			if (CloseHandle(hPlayerThread)) DestroyWindow(hWnd);
		}
		break;

	case WM_DESTROY:
		if (g_hInstPlayer) delete g_hInstPlayer;
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
	}
	return (INT_PTR)FALSE;
}


// Setting Dialog Proc
BOOL CALLBACK SettingDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam){

	static VideoSource VSource;
	static HWND hCmbMidioutDev;
	static HWND hCmbPlayer;
	static std::vector <int> vecMidiDevNo;
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

		// Show Player List
		hCmbPlayer = GetDlgItem(hDlg, IDC_COMBO_PLAYER);
		for (int iPlayerNo = 0; VRPlayerName[iPlayerNo] != NULL; ++iPlayerNo){
			ComboBox_AddString(hCmbPlayer, VRPlayerName[iPlayerNo]);
		}
		ComboBox_SetCurSel(hCmbPlayer, g_VRPlayer);

		// Change Dlg State
		switch (DlgState) {
		case SettingDlgState::DLG1:
			EnableWindow(GetDlgItem(hDlg, IDOKDLG), FALSE);
			ShowWindow(GetDlgItem(hDlg, IDC_WEBCAM), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_VIDEOFILE), SW_HIDE);
			break;

		case SettingDlgState::DLG1ONLY:
			EnableWindow(GetDlgItem(hDlg, IDOKDLG), TRUE);
			ShowWindow(GetDlgItem(hDlg, IDC_DLGNEXT), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_WEBCAM), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_VIDEOFILE), SW_HIDE);
			break;

		case SettingDlgState::DLG2ONLY:
			EnableWindow(GetDlgItem(hDlg, IDOKDLG), TRUE);
			ShowWindow(GetDlgItem(hDlg, IDC_DLGNEXT), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_COMBO_MIDIOUT), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_COMBO_PLAYER), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_STATIC1), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_STATIC2), SW_HIDE);
			ShowWindow(GetDlgItem(hDlg, IDC_WEBCAM), SW_SHOW);
			ShowWindow(GetDlgItem(hDlg, IDC_VIDEOFILE), SW_SHOW);
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
			int iMidioutDevNo = vecMidiDevNo.at(ComboBox_GetCurSel(hCmbMidioutDev));

			// Open Midiout
			if (midiOutOpen(&g_hMidiOut, iMidioutDevNo, 0, 0, CALLBACK_NULL) != MMSYSERR_NOERROR){
				MessageBox(hDlg, _T("Error : Midi port can't open!"), _T("Error"), MB_ICONWARNING | MB_OK);
				return TRUE;
			}

			// Show MidioutDev Name to Status Bar
			TCHAR strBuf[MAX_LOADSTRING] = { 0 };
			midiOutGetDevCaps(iMidioutDevNo, &cap, sizeof(cap));
			wsprintf(strBuf, _T("Midi Out : %s"), cap.szPname);
			SendMessage(g_hStatusBar, SB_SETTEXT, 0, (LPARAM)strBuf);

			// Show Player Name to Status Bar
			wsprintf(strBuf, _T("Player : %s"), VRPlayerName[g_VRPlayer]);
			SendMessage(g_hStatusBar, SB_SETTEXT, 1, (LPARAM)strBuf);

			bool bIsOpenVideo = false;
			if (DlgState != SettingDlgState::DLG1ONLY){

				if (VSource == VideoSource::VIDEOFILE){
					if (OpenVideoFile(hDlg) != 0) bIsOpenVideo = true;
					
				}
				else if (VSource == VideoSource::WEBCAM) {
					if (OpenWebcam(hDlg) != 0) bIsOpenVideo = true;
				}
			}

			if (!bIsOpenVideo) EndDialog(hDlg, IDOK);
			::LeaveCriticalSection(&g_csExclusiveThread);

			return TRUE;
		}

		case IDCANCEL:
			EndDialog(hDlg, IDCANCEL);

			return TRUE;

		case IDC_DLGNEXT:
			if (DlgState == SettingDlgState::DLG1){
				
				// Transition to Inputsrc Sel Dlg
				SetWindowText(hDlg, _T("Input Video"));
				SetWindowText(GetDlgItem(hDlg, IDC_DLGNEXT), _T("Prev"));
				EnableWindow(GetDlgItem(hDlg, IDOKDLG), TRUE);
				ShowWindow(GetDlgItem(hDlg, IDC_COMBO_MIDIOUT), SW_HIDE);
				ShowWindow(GetDlgItem(hDlg, IDC_COMBO_PLAYER), SW_HIDE);
				ShowWindow(GetDlgItem(hDlg, IDC_STATIC1), SW_HIDE);
				ShowWindow(GetDlgItem(hDlg, IDC_STATIC2), SW_HIDE);

				ShowWindow(GetDlgItem(hDlg, IDC_WEBCAM), SW_SHOW);
				ShowWindow(GetDlgItem(hDlg, IDC_VIDEOFILE), SW_SHOW);
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
				DlgState = SettingDlgState::DLG1;
			}
			return TRUE;

		case IDC_WEBCAM:
			VSource = VideoSource::WEBCAM;
			return TRUE;

		case IDC_VIDEOFILE:
			VSource = VideoSource::VIDEOFILE;
			return TRUE;

		case IDC_COMBO_PLAYER:
			g_VRPlayer = (VRPlayer)ComboBox_GetCurSel(hCmbPlayer);
			return TRUE;
		}

	}
	return FALSE;
}


int OpenVideoFile(const HWND &hWnd)
{

	TCHAR szFilePath[MAX_LOADSTRING] = {0};

	OPENFILENAME ofn = { sizeof(ofn) };
	ofn.hwndOwner = hWnd;
	ofn.lpstrFilter = _T("Video File(mp4, AVI)\0*.mp4;*.avi\0");
	ofn.lpstrFile = szFilePath;
	ofn.nMaxFile = MAX_LOADSTRING;
	ofn.nMaxFileTitle = MAX_LOADSTRING;
	ofn.Flags = OFN_FILEMUSTEXIST | OFN_NOCHANGEDIR;
	ofn.lpstrTitle = _T("Open Roll Video File"); 

	if (!GetOpenFileName(&ofn)) return -1;

	std::string filepath;
#ifdef UNICODE
	size_t size(0);
	char buffer[2 * MAX_LOADSTRING + 2] = {0};
	setlocale(LC_CTYPE, "Japanese_Japan.932");
	wcstombs_s(&size, buffer, (size_t)MAX_LOADSTRING, szFilePath, (size_t)MAX_LOADSTRING);
	filepath.assign(buffer);
#else
	filepath = tcVideoFileNameFull;
#endif

	g_strVideoPath = filepath;

	// Check Video Resolution
	cv::VideoCapture dummyCap(filepath);
	if ((dummyCap.get(CV_CAP_PROP_FRAME_WIDTH) != VIDEO_WIDTH) || (dummyCap.get(CV_CAP_PROP_FRAME_HEIGHT) != VIDEO_HEIGHT)){
		MessageBox(hWnd, _T("Video Resultion is not 640x480"), _T("Error"), MB_OK | MB_ICONWARNING);

		return -1;
	}

	// Open Video File
	if(g_CvCap.isOpened()) g_CvCap.release();
	g_CvCap.open(filepath);

	return 0;
}


int OpenWebcam(const HWND &hWnd) 
{
	// Load Webcam Devno
	TCHAR szIniPath[MAX_PATH] = { 0 };
	GetCurrentDirectory(sizeof(szIniPath), szIniPath);
	_stprintf_s(szIniPath, _T("%s\\%s"), szIniPath, SETTING_INI_NAME);
	DWORD dwWebCamDevNo = GetPrivateProfileInt(_T("Initialize Setting"), _T("WebCamDevNo"), 0, szIniPath);

	// Open Webcam
	if (g_CvCap.isOpened()) g_CvCap.release();
	if (!g_CvCap.open(dwWebCamDevNo)) {
		MessageBox(hWnd, _T("Failed to Open Webcam"), _T("Error"), MB_OK | MB_ICONWARNING);

		return -1;
	}

	g_CvCap.set(CV_CAP_PROP_FPS, MAX_g_dwVideoFrameRate);

	return 0;
}


HWND CreateStatusBar(const HWND &hWnd){

	int sb_pos[3] = { 300, 500, -1 };

	HWND status = CreateWindowEx(0, STATUSCLASSNAME, NULL, WS_CHILD | SBARS_SIZEGRIP | CCS_BOTTOM | WS_VISIBLE,
		0, 0, 0, 0, hWnd, (HMENU)MY_STATUS, hInst, NULL);

	SendMessage(status, SB_SETPARTS, 3, (LPARAM)sb_pos);
	SendMessage(status, SB_SETTEXT, 0, (LPARAM)_T("Midi Out"));
	SendMessage(status, SB_SETTEXT, 1, (LPARAM)_T("Player "));
	SendMessage(status, SB_SETTEXT, 2, (LPARAM)_T("Frames"));

	return status;
}


int CreateButton(const HWND &hWnd){
	
	// Play/Stop Button
	g_hBtnStartEngine = CreateWindow(_T("BUTTON"),		
		_T("Play"), WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON ,
		645,15, 110, 40, hWnd, (HMENU)IDC_BTN_START_ENGINE, hInst, NULL);
	SendMessage(g_hBtnStartEngine, WM_SETFONT, (WPARAM)CreateFont(22, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET, 
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE,_T("Arial")),MAKELPARAM(TRUE,0));

	// Midi On/Off Button
	g_hBtnMidiOn = CreateWindow(_T("BUTTON"),
		_T("Midi On"), WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
		645, 65, 110, 40, hWnd, (HMENU)IDC_BTN_MIDION, hInst, NULL);
	SendMessage(g_hBtnMidiOn, WM_SETFONT, (WPARAM)CreateFont(22, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Video Frame Rate Slider
	HWND staticTxt1 = CreateWindow(_T("STATIC"), _T(" Frame Rate"), WS_CHILD | WS_VISIBLE, 645, 115, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(staticTxt1, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hSlFrameRate = CreateWindowEx(0, TRACKBAR_CLASS, NULL, WS_CHILD | WS_VISIBLE | TBS_AUTOTICKS, 645, 130, 110, 45, hWnd, (HMENU)IDC_SLIDER1, hInst, NULL);
	SendMessage(g_hSlFrameRate, TBM_SETRANGE, TRUE, MAKELPARAM(10, MAX_g_dwVideoFrameRate));
	SendMessage(g_hSlFrameRate, TBM_SETTICFREQ, 10, 0);
	SendMessage(g_hSlFrameRate, TBM_SETPAGESIZE, 0, 5);
	SendMessage(g_hSlFrameRate, TBM_SETPOS, TRUE, g_dwVideoFrameRate);

	// Max Velocity text
	HWND staticTxt2 = CreateWindow(_T("STATIC"), _T("Max Velocity"), WS_CHILD | WS_VISIBLE, 645, 175, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(staticTxt2, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hStMaxVelo = CreateWindow(_T("STATIC"), _T("90"), WS_CHILD | WS_VISIBLE, 645, 190, 110, 20, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStMaxVelo, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Min Velocity text
	HWND staticTxt3 = CreateWindow(_T("STATIC"), _T("Min Velocity"), WS_CHILD | WS_VISIBLE, 645, 210, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(staticTxt3, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hStMinVelo = CreateWindow(_T("STATIC"), _T("90"), WS_CHILD | WS_VISIBLE, 645, 225, 110, 25, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStMinVelo, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Bass Velocity text
	HWND staticTxt4 = CreateWindow(_T("STATIC"), _T("Bass Velocity"), WS_CHILD | WS_VISIBLE, 645, 250, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(staticTxt4, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hStBassVelo = CreateWindow(_T("STATIC"), _T("0"), WS_CHILD | WS_VISIBLE, 645, 265, 110, 20, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStBassVelo, WM_SETFONT, (WPARAM)CreateFont(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Treble Velocity text
	HWND staticTxt5 = CreateWindow(_T("STATIC"), _T("Treble Velocity"), WS_CHILD | WS_VISIBLE, 645, 285, 110, 15, hWnd, NULL, hInst, NULL);
	SendMessage(staticTxt5, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	g_hStTrebleVelo = CreateWindow(_T("STATIC"), _T("0"), WS_CHILD | WS_VISIBLE, 645, 300, 110, 25, hWnd, NULL, hInst, NULL);
	SendMessage(g_hStTrebleVelo, WM_SETFONT, (WPARAM)CreateFont(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Tracking Offset text
	HWND staticTxt6 = CreateWindow(_T("STATIC"), _T("Tracker Offset"), WS_CHILD | WS_VISIBLE, 645, 325, 110, 20, hWnd, NULL, hInst, NULL);
	SendMessage(staticTxt6, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	g_stRollOffset = CreateWindow(_T("STATIC"), _T("0"), WS_CHILD | WS_VISIBLE, 645, 345, 110, 25, hWnd, NULL, hInst, NULL);
	SendMessage(g_stRollOffset, WM_SETFONT, (WPARAM)CreateFont(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Tracking Offset Slider
	CreateWindow(UPDOWN_CLASS, _T("SP_RED"), WS_CHILD | WS_VISIBLE | WS_TABSTOP | UDS_WRAP | UDS_ARROWKEYS | UDS_ALIGNRIGHT | UDS_HORZ
		| UDS_SETBUDDYINT ,685, 345, 60, 25,hWnd, (HMENU)(IDC_SPIN_TRACKING_OFFSET),hInst, NULL);

	// Note-On Frame text
	HWND staticTxt7 = CreateWindow(_T("STATIC"), _T("Note-On Frames"), WS_CHILD | WS_VISIBLE, 645, 370, 110, 20, hWnd, NULL, hInst, NULL);
	SendMessage(staticTxt7, WM_SETFONT, (WPARAM)CreateFont(16, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));
	
	g_stNoteOnFrame = CreateWindow(_T("STATIC"), _T("1"), WS_CHILD | WS_VISIBLE, 645, 390, 110, 25, hWnd, NULL, hInst, NULL);
	SendMessage(g_stNoteOnFrame, WM_SETFONT, (WPARAM)CreateFont(20, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, ANSI_CHARSET,
		OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, _T("Arial")), MAKELPARAM(TRUE, 0));

	// Note-on Frame Slider
	CreateWindow(UPDOWN_CLASS, _T("SP_RED"), WS_CHILD | WS_VISIBLE | WS_TABSTOP | UDS_WRAP | UDS_ARROWKEYS | UDS_ALIGNRIGHT | UDS_HORZ
		| UDS_SETBUDDYINT, 685, 390, 60, 25, hWnd, (HMENU)(IDC_SPIN_NOTEONFRAMES), hInst, NULL);


	return 0;
}

static void LoadTrackingOffset(std::vector< std::pair<UINT, INT> > &arTrackingOffsetVal)
{
	arTrackingOffsetVal.clear();
	if (g_bIsTrackingSetMode) return;

	std::string strPath = g_strVideoPath.substr(0, g_strVideoPath.find_last_of(".")) + "_Tracking.txt";
	FILE *fp = NULL;
	fopen_s(&fp, strPath.c_str(), "r");
	if (fp) {
		UINT uiFrames = 0;
		INT iOffset = 0;
		while (fscanf_s(fp, "%u : %d", &uiFrames, &iOffset) != EOF) {
			arTrackingOffsetVal.push_back(std::pair<UINT, UINT>(uiFrames, iOffset));
		}

		fclose(fp);
	}

	return;
}


DWORD WINAPI PlayerThread(LPVOID lpdata)
{
	DWORD nPrevFPS = 0;
	double dPassTime = 0;
	LARGE_INTEGER nStartTime, nEndTime, nFreq;
	memset(&nFreq, 0x00, sizeof(nFreq));
	memset(&nStartTime, 0x00, sizeof(nStartTime));
	memset(&nEndTime, 0x00, sizeof(nEndTime));
	QueryPerformanceFrequency(&nFreq);
	timeBeginPeriod(1);

	// For Auto Tracking
	std::vector< std::pair<UINT, INT> > arTrackingOffsetVal;
	std::vector< std::pair<UINT, INT> >::iterator it;

	while (!g_bAppEndFlag){

		QueryPerformanceCounter(&nStartTime);
		::EnterCriticalSection(&g_csExclusiveThread);

		static bool bLastFrame = false;
		UINT iCurFrame = (UINT)g_CvCap.get(CV_CAP_PROP_POS_FRAMES);
		if (iCurFrame == 0) bLastFrame = false;

		if ((g_bEngineStart || iCurFrame == 0) && !bLastFrame){

			cv::Mat frame;
			if (g_CvCap.grab() && g_CvCap.retrieve(frame)){
				bLastFrame = false;

				// Load AutoTracking File
				if (iCurFrame == 0) {
					LoadTrackingOffset(arTrackingOffsetVal);
					it = arTrackingOffsetVal.begin();
				}

				// Do AutoTracking
				if (!g_bIsTrackingSetMode && it != arTrackingOffsetVal.end() && iCurFrame == it->first){
					
					g_hInstPlayer->SetRollOffset(it->second);
					TCHAR bufStr[MAX_LOADSTRING] = { 0 };
					wsprintf(bufStr, TEXT("%d"), it->second);
					SetWindowText(g_stRollOffset, bufStr);
					it++;
#ifdef DEBUG
					static TCHAR strBuf[20];
					wsprintf(strBuf, _T("%u frames\n"), uiCurFrame);
					OutputDebugString(strBuf);
#endif // DEBUG
				}

				// Emulates Roll Image to Midi Siganl
				g_hInstPlayer->SetFrameRate(nPrevFPS);
				g_hInstPlayer->Emulate(frame, g_hdcImage, g_hMidiOut);

				static RECT rcClipping = { 0, 0, VIDEO_WIDTH, VIDEO_HEIGHT };
				InvalidateRect((HWND)lpdata, &rcClipping, FALSE);
			}
			else {
				bLastFrame = true;
			}
		}
		::LeaveCriticalSection(&g_csExclusiveThread);

		// Wait for Set FrameRate
		do{
			QueryPerformanceCounter(&nEndTime);
			dPassTime = (nEndTime.QuadPart - nStartTime.QuadPart) * 1000 / (double)nFreq.QuadPart;
		} while ((double)1000 / g_dwVideoFrameRate > dPassTime);


		// Show FrameRate to Status Bar
		DWORD nCurFPS = (DWORD)round(1000 / dPassTime);
		if (nPrevFPS != nCurFPS){
			TCHAR strBuf[20];
			wsprintf(strBuf, _T("Frames : %d fps"), nCurFPS);
			SendMessage(g_hStatusBar, SB_SETTEXT, 2, (LPARAM)strBuf);
		}
		nPrevFPS = nCurFPS;
	}

	timeEndPeriod(1);

	return 0;
}