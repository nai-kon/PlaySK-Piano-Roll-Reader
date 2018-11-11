#pragma once

#include "Player.h"
#include <mmsystem.h>
#include <opencv2/core/core.hpp>


class AmpicoA : public Player{

private:
	// hole position
	int m_BassSlowCres_x;
	int m_BassLv2_x;
	int m_BassLv4_x;
	int m_BassFastCres_x;
	int m_BassLv6_x;
	int m_BassCancel_x;
	int m_ReRoll_x;
	int m_TrebleCancel_x;
	int m_TrebleLv6_x;
	int m_TrebleFastCres_x;
	int m_TrebleLv4_x;
	int m_TrebleLv2_x;
	int m_TrebleSlowCres_x;

	// hole size
	int m_SlowCresHole_width;
	int m_SlowCresHole_height;
	int m_FastCresHole_width;
	int m_FastCresHole_height;
	int m_SusteinHole_width;
	int m_SusteinHole_height;
	int m_SoftHole_width;
	int m_SoftHole_height;

	// On Off TH
	int mSusuteinOnTH, mSusuteinOffTH;
	int mSoftOnTH, mSoftOffTH;
	int mIntensityTH;

	// Intensity
	// [0]:all off [1]:2 [2]:4 [3]:2+4 [4]:6 [5]:2+6 [6]:4+6 [7]:2+4+6
	double m_BassIntensity[8];
	double m_TrebleIntensity[8];
	bool m_bBassLv2;
	bool m_bBassLv4;
	bool m_bBassLv6;
	bool m_bTrebleLv2;
	bool m_bTrebleLv4;
	bool m_bTrebleLv6;
	bool m_bBassCancel, m_bTrebleCancel;

	// Amplifier
	double m_dAmpVelo;
	double m_dMaxAmpVelo;
	bool m_bAmpOn;

	// Crescendo
	bool m_bBassSlowCresOn, m_bBassFastCresOn;
	bool m_bTrebleSlowCresOn, m_bTrebleFastCresOn;

	double m_BassMaxVelo, m_BassMinVelo;
	double m_TrebleMaxVelo, m_TrebleMinVelo;
public:
	AmpicoA();
	virtual ~AmpicoA(){}
	virtual int Emulate(cv::Mat &frame, HDC &g_hdcImage, const HMIDIOUT &hm);
	virtual int LoadPlayerSettings();
	virtual int NoteAllOff(const HMIDIOUT &hm);

private:
	int ReadExpressionHoles(cv::Mat &frame, const HMIDIOUT &hm);
	int CalcBassVelocity();
	int BassIntensityCurv(double &dintensityVelo);
	int BassCrescendoCurv(double &dCresVelo);
	int CalcTrebleVelocity();
	int TrebleIntensityCurv(double &dintensityVelo);
	int TrebleCrescendoCurv(double &dCresVelo);
	int CalcAmplifier();	// should emulate...

};


