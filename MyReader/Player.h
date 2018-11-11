#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>

#define KeyNum				88
#define MAXNoteOnFrames		10


class Player{
	
protected:

	// Tracker Hole Status  // 0:off 1:off->on 2:on 3:on->off
	enum NoteState {
		offTriger = -2,
		off = -1,
		onTriger = 1,
		on = 2,
	};

	// NotePosition
	int m_iSusteinPedalHoleX, m_iSoftPedalHoleX;
	int m_iNoteHoleWidth, m_iNoteHoleHeigth;
	int m_iPedalHoleWidth, m_iPedalHoleHeight;
	int m_iNote_x[KeyNum];

	int m_iLowestNoteNo, m_iHighestNoteNo;	// 0 to 87 on 88-notes Tracker
	int m_iStackDevide;						// Stack Devide Point

	char m_cNoteOn[KeyNum];	
	char m_cNoteOnCnt[KeyNum];
	char m_cSusteinPedalOn, m_cSoftPedalOn;

	// On-Off Image Thereshold
	int m_iNoteOnTH, m_iNoteOffTH;
	int m_iPedalOnTH, m_iPedalOffTH;

	// Offset
	int m_iTrackingOffset;
	int m_iNoteOnFrames;

	double m_dFrameRate;

	int m_iBassStackVelo, m_iTrebleStackVelo;
	int m_iMinVelocity, m_iMaxVelocity;

	bool m_bEmulateOn;


public:
	Player();
	virtual ~Player();
	virtual int Emulate(cv::Mat &frame, HDC &g_hdcImage, const HMIDIOUT &hm);
	virtual int LoadPlayerSettings();
	virtual int NoteAllOff(const HMIDIOUT &hm);
	int GetMinVelocity() { return m_iMinVelocity; }
	int GetMaxVelocity() { return m_iMaxVelocity; }
	int GetBassVelocity() { return m_iBassStackVelo; }
	int GetTrebleVelocity() { return m_iTrebleStackVelo; }
	void SetEmulateOn() { m_bEmulateOn = true; }
	void SetEmulateOff() { m_bEmulateOn = false; }
	void SetRollOffset(int offset) { m_iTrackingOffset = offset; }
	int GetRollOffset() { return m_iTrackingOffset; }
	void SetNoteOnFrames(int iFrames) { m_iNoteOnFrames = iFrames; }
	int GetNoteOnFrames() { return m_iNoteOnFrames; }
	void SetFrameRate(double ifps){ m_dFrameRate = ifps; }

protected:

	void SendMidiMsg(const HMIDIOUT &hm);

	void inline NoteOnMsg(int key, int velocity, const HMIDIOUT &g_hMidiOut) const{
		DWORD dwMsg = velocity << 16 | key << 8 | 0x90;
		midiOutShortMsg(g_hMidiOut, dwMsg);
	}
	void inline NoteOffMsg(int key, const HMIDIOUT &g_hMidiOut) const{
		static const int iNoteOffVelocity = 90; 
		DWORD dwMsg = iNoteOffVelocity << 16 | key << 8 | 0x80;
		midiOutShortMsg(g_hMidiOut, dwMsg);
	}
	void inline SusteinP(bool status, const HMIDIOUT &g_hMidiOut) const{
		if (status) midiOutShortMsg(g_hMidiOut, 127 << 16 | 64 << 8 | 0xb0);
		else midiOutShortMsg(g_hMidiOut, 64 << 8 | 0xb0);
	}
	void inline SoftP(bool status, const HMIDIOUT &g_hMidiOut) const{
		if (status) midiOutShortMsg(g_hMidiOut, 127 << 16 | 67 << 8 | 0xb0);
		else midiOutShortMsg(g_hMidiOut, 67 << 8 | 0xb0);
	}

};