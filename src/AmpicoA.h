#pragma once

#include "Player.h"
#include <mmsystem.h>
#include <opencv2/core/core.hpp>


class AmpicoA : public Player{

public:
	AmpicoA();
	virtual ~AmpicoA() {}
	virtual void EmulateVelocity(cv::Mat &frame);
	virtual int LoadPlayerSettings(LPCTSTR config_path);
	virtual int NoteAllOff(const HMIDIOUT &hm);
	virtual int GetMinVelocity();
	virtual int GetMaxVelocity();

private:

	// expression holes
	TRACKER_HOLE m_rcBassSlowCresc, m_rcTrebleSlowCresc;
	TRACKER_HOLE m_rcBassFastCresc, m_rcTrebleFastCresc;
	TRACKER_HOLE m_rcBassCancel, m_rcTrebleCancel;
	TRACKER_HOLE m_rcBassIntensity[3], m_rcTrebleIntensity[3];
	TRACKER_HOLE m_rcReRoll;

	// Intensity
	// [0]:all off [1]:2 [2]:4 [3]:6(2+4) [4]:2+6 [5]:4+6 [6]:2+4+6
	double m_dBassIntensity[7];
	double m_dTrebleIntensity[7];

	bool m_bBassLv2, m_bTrebleLv2;
	bool m_bBassLv4, m_bTrebleLv4;
	bool m_bBassLv6, m_bTrebleLv6;
	bool m_bBassCancel, m_bTrebleCancel;
	bool m_bBassSlowCresOn, m_bBassFastCresOn;
	bool m_bTrebleSlowCresOn, m_bTrebleFastCresOn;

	double m_dBassMaxVelo, m_dBassMinVelo;
	double m_dTrebleMaxVelo, m_dTrebleMinVelo;

	double m_dSlowCrescSec;
	double m_dFastCrescSec;
	double m_dFullIntensityDelay;
	

	void CheckExpressionHoles(cv::Mat &frame);
	void CalcBassVelocity();
	void CalcTrebleVelocity();
	void BassIntensityCurv(double &dintensityVelo);
	void TrebleIntensityCurv(double &dintensityVelo);
	void BassCrescendoCurv(double &dCresVelo);
	void TrebleCrescendoCurv(double &dCresVelo);
	//int CalcAmplifier();	// should emulate...


};


