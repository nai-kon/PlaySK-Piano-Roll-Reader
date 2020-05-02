#pragma once

#include "Player.h"
#include <mmsystem.h>
#include <opencv2/core/core.hpp>


class DuoArt : public Player{

public:
	DuoArt();
	virtual ~DuoArt() {}
	virtual void EmulateVelocity(cv::Mat &frame);
	virtual int LoadPlayerSettings(LPCTSTR config_path);
	virtual int GetMinVelocity();
	virtual int GetMaxVelocity();

private:
	// expression holes
	TRACKER_HOLE m_rcBassSnakebite, m_rcTrebleSnakebite;
	TRACKER_HOLE m_rcAccomp[4], m_rcTheme[4];

	double m_dTheme8 , m_dTheme4, m_dTheme2 , m_dTheme1;
	double m_dAccomp8 , m_dAccomp4 , m_dAccomp2 , m_dAccomp1;
	bool m_bBassAccent, m_bTrebleAccent;
	int m_iAccompMinVelo, m_iAccompMaxVelo;
	int m_iThemeMinVelo, m_iThemeMaxVelo;
	

	void CheckExpressionHoles(cv::Mat &frame);
	void CalcVelocity();

	void Accomp8(bool bActive){
		if (bActive){
			m_dAccomp8 += 0.4;
			if (m_dAccomp8 > 8) m_dAccomp8 = 8;
		}
		else{
			m_dAccomp8 -= 0.4;
			if (m_dAccomp8 < 0) m_dAccomp8 = 0;
		}
	}
	void Accomp4(bool bActive){
		if (bActive){
			m_dAccomp4 += 0.2;
			if (m_dAccomp4 > 4) m_dAccomp4 = 4;
		}
		else{
			m_dAccomp4 -= 0.2;
			if (m_dAccomp4 < 0) m_dAccomp4 = 0;
		}
	}
	void Accomp2(bool bActive){
		if (bActive){
			m_dAccomp2 += 0.1;
			if (m_dAccomp2 > 2) m_dAccomp2 = 2;
		}
		else{
			m_dAccomp2 -= 0.1;
			if (m_dAccomp2 < 0) m_dAccomp2 = 0;
		}
	}
	void Accomp1(bool bActive){
		if (bActive){
			m_dAccomp1 += 0.06;
			if (m_dAccomp1 > 1) m_dAccomp1 = 1;
		}
		else{
			m_dAccomp1 -= 0.06;
			if (m_dAccomp1 < 0) m_dAccomp1 = 0;
		}
	}

	void Theme8(bool bActive){
		if (bActive){
			m_dTheme8 += 0.4;
			if (m_dTheme8 > 8) m_dTheme8 = 8;
		}
		else{
			m_dTheme8 -= 0.4;
			if (m_dTheme8 < 0) m_dTheme8 = 0;
		}
	}
	void Theme4(bool bActive){
		if (bActive){
			m_dTheme4 += 0.2;
			if (m_dTheme4 > 4) m_dTheme4 = 4;
		}
		else{
			m_dTheme4 -= 0.2;
			if (m_dTheme4 < 0) m_dTheme4 = 0;
		}
	}
	void Theme2(bool bActive){
		if (bActive){
			m_dTheme2 += 0.1;
			if (m_dTheme2 > 2) m_dTheme2 = 2;
		}
		else{
			m_dTheme2 -= 0.1;
			if (m_dTheme2 < 0) m_dTheme2 = 0;
		}
	}
	void Theme1(bool bActive){
		if (bActive){
			m_dTheme1 += 0.06;
			if (m_dTheme1 > 1) m_dTheme1 = 1;
		}
		else{
			m_dTheme1 -= 0.06;
			if (m_dTheme1 < 0) m_dTheme1 = 0;
		}
	}
};


