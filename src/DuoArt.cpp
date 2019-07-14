
#include "stdafx.h"
#include "Player.h"
#include "DuoArt.h"



DuoArt::DuoArt()
{ 
	m_bBassAccent = false;
	m_bTrebleAccent = false;
	m_dTheme1 = 0;
	m_dTheme2 = 0;
	m_dTheme4 = 0;
	m_dTheme8 = 0;
	m_dAccomp1 = 0;
	m_dAccomp2 = 0;
	m_dAccomp4 = 0;
	m_dAccomp8 = 0;
	m_uiStackSplitPoint = 43;
}



int DuoArt::LoadPlayerSettings()
{
	std::ifstream ifs("config\\Duo-Art_tracker.json");
	std::string err, strjson((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
	json11::Json json = json11::Json::parse(strjson, err);

	auto obj = json["expression"]["accomp"];
	m_iAccompMinVelo = obj["min"].int_value();
	m_iAccompMaxVelo = obj["max"].int_value();

	obj = json["expression"]["theme"];
	m_iThemeMinVelo = obj["min"].int_value();
	m_iThemeMaxVelo = obj["max"].int_value();

	obj = json["tracker_holes"];
	SetHoleRectFromJsonObj(obj["sustain"], m_rcSustainPedal);
	SetHoleRectFromJsonObj(obj["soft"], m_rcSoftPedal);
	SetHoleRectFromJsonObj(obj["bass_snakebite"], m_rcBassSnakebite);
	SetHoleRectFromJsonObj(obj["treble_snakebite"], m_rcTrebleSnakebite);
	SetHoleRectListFromJsonObj(obj["accomp"], m_rcAccomp, 4);
	SetHoleRectListFromJsonObj(obj["theme"], m_rcTheme, 4);
	SetHoleRectListFromJsonObj(obj["note"], m_rcNote, KeyNum);

	// set default velocity
	m_iBassStackVelo = m_iTrebleStackVelo = m_iAccompMinVelo;

	if (err.size() > 0) return -1;
	return 0;
}

int DuoArt::GetMinVelocity()
{
	return m_iAccompMinVelo;
}
int DuoArt::GetMaxVelocity()
{
	return m_iThemeMaxVelo;
}


void DuoArt::EmulateVelocity(cv::Mat &frame)
{
	// Read Control Holes
	CheckExpressionHoles(frame);

	// Calc Velocity
	CalcVelocity();

}

// Scan Expression Holes from Video Frame
void DuoArt::CheckExpressionHoles(cv::Mat &frame)
{
	double dAvg = 0;

	// Duo-Art Accomp Holes check(Accomp lv.1->lv.8)
	for (int n = 0; n < 4; n++) {
		dAvg = GetAvgHoleBrightness(frame, m_rcAccomp[n]);
		bool bActive = (dAvg < m_rcAccomp[n].th_on && m_bEmulateOn) ? true : false;

		switch (n) {
		case 0:
			Accomp1(bActive);
			break;
		case 1:
			Accomp2(bActive);
			break;
		case 2:
			Accomp4(bActive);
			break;
		case 3:
			Accomp8(bActive);
			break;
		}
		DrawHole(frame, m_rcAccomp[n], bActive);
	}

	// Duo-Art Theme Holes check(Theme lv.1->lv.8)
	for (int n = 0; n < 4; n++) {
		dAvg = GetAvgHoleBrightness(frame, m_rcTheme[n]);
		bool bActive = (dAvg < m_rcTheme[n].th_on && m_bEmulateOn) ? true : false;

		switch (n) {
		case 0:
			Theme1(bActive);
			break;
		case 1:
			Theme2(bActive);
			break;
		case 2:
			Theme4(bActive);
			break;
		case 3:
			Theme8(bActive);
			break;
		}
		DrawHole(frame, m_rcTheme[n], bActive);
	}

	// Check Bass Snakebite
	static int iBassAccentDelayCnt = 0;
	dAvg = GetAvgHoleBrightness(frame, m_rcBassSnakebite);
	if ((dAvg < m_rcBassSnakebite.th_on && m_bEmulateOn) || iBassAccentDelayCnt > 0) {
		if (dAvg < m_rcBassSnakebite.th_on && m_bEmulateOn) iBassAccentDelayCnt = 3;
		m_bBassAccent = true;
	}
	else {
		m_bBassAccent = false;
	}
	if (iBassAccentDelayCnt >= 0)	iBassAccentDelayCnt--;
	DrawHole(frame, m_rcBassSnakebite, m_bBassAccent);

	// Check Treble Snakebite
	static int iTrebleAccentDelayCnt = 0;
	dAvg = GetAvgHoleBrightness(frame, m_rcTrebleSnakebite);
	if ((dAvg < m_rcTrebleSnakebite.th_on && m_bEmulateOn) || iTrebleAccentDelayCnt > 0) {
		if (dAvg < m_rcTrebleSnakebite.th_on && m_bEmulateOn) iTrebleAccentDelayCnt = 3;
		m_bTrebleAccent = true;
	}
	else {
		m_bTrebleAccent = false;
	}
	DrawHole(frame, m_rcTrebleSnakebite, m_bTrebleAccent);
	if (iTrebleAccentDelayCnt >= 0)	iTrebleAccentDelayCnt--;

	return;
}


void DuoArt::CalcVelocity()
{
	// Calc Accomp Velocity
	double dAccompVelo = m_iAccompMinVelo + (m_dAccomp1 + m_dAccomp2 + m_dAccomp4 + m_dAccomp8)*((m_iAccompMaxVelo - m_iAccompMinVelo) / 15.0);
	// Calc Theme Velocity
	double dThemeVelo = m_iThemeMinVelo + (m_dTheme1 + m_dTheme2 + m_dTheme4 + m_dTheme8)*((m_iThemeMaxVelo - m_iThemeMinVelo) / 15.0);

	// Calc Bass Stack Velocity
	static int iPrevBassStackVelo = m_iAccompMinVelo;
	const static int iAccentDelayFrames = 1;
	if (m_bBassAccent) {
		if (iPrevBassStackVelo < dThemeVelo) {
			m_iBassStackVelo += (int)((dThemeVelo - iPrevBassStackVelo) / (double)iAccentDelayFrames);
		}
	}
	else {
		if (iPrevBassStackVelo > dAccompVelo) {
			m_iBassStackVelo -= (int)((iPrevBassStackVelo - dAccompVelo) / (double)iAccentDelayFrames);
		}
		else {

			m_iBassStackVelo = (int)dAccompVelo;
		}
	}

	// Calc Treble Stack Velocity
	static int iPrevTrebleStackVelo = m_iAccompMinVelo;
	if (m_bTrebleAccent) {
		if (iPrevTrebleStackVelo < dThemeVelo) {
			m_iTrebleStackVelo += (int)((dThemeVelo - iPrevTrebleStackVelo) / (double)iAccentDelayFrames);
		}
	}
	else {
		if (iPrevTrebleStackVelo > dAccompVelo) {
			m_iTrebleStackVelo -= (int)((iPrevTrebleStackVelo - dAccompVelo) / (double)iAccentDelayFrames);
		}
		else {
			m_iTrebleStackVelo = (int)dAccompVelo;
		}
	}

	// Delay Count
	static int BassVelDelay[MAXNoteOnFrames + 2] = { 0 };
	static int TrebleVelDelay[MAXNoteOnFrames + 2] = { 0 };
	BassVelDelay[0] = m_iBassStackVelo;
	TrebleVelDelay[0] = m_iTrebleStackVelo;
	m_iBassStackVelo = BassVelDelay[m_iNoteOnFrames + 1];
	m_iTrebleStackVelo = TrebleVelDelay[m_iNoteOnFrames + 1];

	for (int i = m_iNoteOnFrames + 1; i > 0; i--) {
		int temp = BassVelDelay[i - 1];
		BassVelDelay[i] = temp;
		temp = TrebleVelDelay[i - 1];
		TrebleVelDelay[i] = temp;
	}

	iPrevBassStackVelo = m_iBassStackVelo;
	iPrevTrebleStackVelo = m_iTrebleStackVelo;

	return;
}