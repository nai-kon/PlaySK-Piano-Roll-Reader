#pragma once

#include <mmsystem.h>
#include <opencv2/core/core.hpp>
#include "json11.hpp"

#define KeyNum				88
#define MAXNoteOnFrames		10


typedef struct tagTRACKER_HOLE {
	int x;
	int y;
	int w;
	int h;
	double on_apature;	// note on hole apature ratio
	double off_apature;	// note off hole apature ratio
} TRACKER_HOLE;


class Player{

public:
	Player();
	virtual ~Player();
	int Emulate(cv::Mat &frame, const HMIDIOUT &hm);
	virtual int LoadPlayerSettings(LPCTSTR config_path);
	virtual int NoteAllOff(const HMIDIOUT &hm);
	virtual int GetMinVelocity();
	virtual int GetMaxVelocity();
	int GetBassVelocity()				{ return m_iBassStackVelo; }
	int GetTrebleVelocity()				{ return m_iTrebleStackVelo; }
	void SetEmulateOn()					{ m_bEmulateOn = true; }
	void SetEmulateOff()				{ m_bEmulateOn = false; }
	void SetRollOffset(int iOffset)		{ m_iTrackingOffset = iOffset; }
	int GetRollOffset()					{ return m_iTrackingOffset; }
	void SetNoteOnFrames(int iFrames)	{ m_iNoteOnFrames = iFrames; }
	int GetNoteOnFrames()				{ return m_iNoteOnFrames; }
	void SetFrameRate(double dfps)		{ m_dFrameRate = dfps; }
	int GetTrackerOffset(const cv::Mat &frame);

protected:
	// tracker hole status  // -2:on->off -1:off 1:off->on 2:on 
	enum NoteState {
		offTriger = -2,
		off = -1,
		onTriger = 1,
		on = 2,
	};
	NoteState m_NoteOn[KeyNum];
	NoteState m_SusteinPedalOn, m_SoftPedalOn;

	// tracker hole 
	TRACKER_HOLE m_rcSustainPedal, m_rcSoftPedal;
	TRACKER_HOLE m_rcNote[KeyNum];

	// split point  
	// bass < [split point] <= treble, with 0 start index
	UINT m_uiStackSplitPoint;

	// note-on delay
	int m_iNoteOnFrames;
	int m_iNoteOnCnt[KeyNum];

	int m_iTrackingOffset;
	double m_dFrameRate;
	int m_iBassStackVelo, m_iTrebleStackVelo;
	bool m_bEmulateOn;

	bool m_bIsDarkHole;
	int m_iHoleOnth;	// hole on pix threshold
	
	virtual void EmulateVelocity(cv::Mat &frame);
	void EmulatePedal(cv::Mat &frame);
	void EmulateNote(cv::Mat &frame);
	double GetHoleApatureRatio(cv::Mat &frame, const TRACKER_HOLE &hole);
	bool isHoleOn(double dApatureRatio, double dOnRatio);
	bool isHoleOff(double dApatureRatio, double dOffRatio);
	void DrawHole(cv::Mat &frame, const TRACKER_HOLE &hole, bool hole_on);
	void SendMidiMsg(const HMIDIOUT &hm);
	void SetHoleRectFromJsonObj(const json11::Json json, TRACKER_HOLE &rcSetHole);
	void SetHoleRectListFromJsonObj(const json11::Json json, TRACKER_HOLE *prcSetHole, UINT rect_cnt);

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