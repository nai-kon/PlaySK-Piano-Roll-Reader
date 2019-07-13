#include "stdafx.h"
#include "AmpicoA.h"

#define _USE_MATH_DEFINES
#include <math.h>

//#define _AMPICO_LINEAR_CRESCENDO

AmpicoA::AmpicoA()
{
	for (int i = 0; i < 7; i++){
		m_dBassIntensity[i] = 0;
		m_dTrebleIntensity[i] = 0;
	}

	m_bBassLv2 = false;
	m_bBassLv4 = false;
	m_bBassLv6 = false;
	m_bTrebleLv2 = false;
	m_bTrebleLv4 = false;
	m_bTrebleLv6 = false;
	m_bBassCancel = false;
	m_bTrebleCancel = false;
	m_bBassSlowCresOn = false;
	m_bBassFastCresOn = false;
	m_bTrebleSlowCresOn = false;
	m_bTrebleFastCresOn = false;

	m_uiStackSplitPoint = 44;
}

int AmpicoA::NoteAllOff(const HMIDIOUT &hm)
{
	m_bBassCancel = true;
	m_bTrebleCancel = true;
	Player::NoteAllOff(hm);

	return 0;
}


int AmpicoA::LoadPlayerSettings()
{
	std::ifstream ifs("AmpicoA_tracker.json");
	std::string err, strjson((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
	json11::Json json = json11::Json::parse(strjson, err);

	auto obj = json["expression"];
	std::vector<json11::Json> vec = obj["bass_intensity"].array_items();
	for (UINT i = 0; i < 7; i++) {
		m_dBassIntensity[i] = vec[i].int_value();
	}
	vec = obj["treble_intensity"].array_items();
	for (UINT i = 0; i < 7; i++) {
		m_dTrebleIntensity[i] = vec[i].int_value();
	}

	m_dSlowCrescSec = obj["slow_cresc_sec"].number_value();
	m_dFastCrescSec = obj["fast_cresc_sec"].number_value();
	m_dFullIntensityDelay = obj["full_intensity_delay"].number_value();

	obj = json["tracker_holes"];
	SetHoleRectFromJsonObj(obj["sustain"], m_rcSustainPedal);
	SetHoleRectFromJsonObj(obj["soft"], m_rcSoftPedal);
	SetHoleRectFromJsonObj(obj["bass_slow_cresc"], m_rcBassSlowCresc);
	SetHoleRectFromJsonObj(obj["bass_fast_cresc"], m_rcBassFastCresc);
	SetHoleRectFromJsonObj(obj["treble_slow_cresc"], m_rcTrebleSlowCresc);
	SetHoleRectFromJsonObj(obj["treble_fast_cresc"], m_rcTrebleFastCresc);
	SetHoleRectListFromJsonObj(obj["bass_intensity"], m_rcBassIntensity, 3);
	SetHoleRectFromJsonObj(obj["bass_cancel"], m_rcBassCancel);
	SetHoleRectListFromJsonObj(obj["treble_intensity"], m_rcTrebleIntensity, 3);
	SetHoleRectFromJsonObj(obj["treble_cancel"], m_rcTrebleCancel);
	SetHoleRectListFromJsonObj(obj["note"], m_rcNote, KeyNum);
	SetHoleRectFromJsonObj(obj["re-roll"], m_rcReRoll);

	m_dBassMinVelo = m_dBassIntensity[0];
	m_dBassMaxVelo = m_dBassIntensity[6];
	m_dTrebleMinVelo = m_dTrebleIntensity[0];
	m_dTrebleMaxVelo = m_dTrebleIntensity[6];

	if (err.size() > 0) return -1;
	return 0;
}

int AmpicoA::GetMinVelocity()
{
	return (int)std::min(m_dBassIntensity[0], m_dTrebleIntensity[0]);
}
int AmpicoA::GetMaxVelocity() 
{
	return (int)std::min(m_dBassIntensity[6], m_dTrebleIntensity[6]);
}

void AmpicoA::EmulateVelocity(cv::Mat &frame)
{
	// Read Control Holes
	CheckExpressionHoles(frame);

	// Calc Velocity
	CalcBassVelocity();
	CalcTrebleVelocity();

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
}


// Scan Intensity Holes from Video Frame
void AmpicoA::CheckExpressionHoles(cv::Mat &frame)
{
	// Bass Cancel
	double dAvg = GetAvgHoleBrightness(frame, m_rcBassCancel);
	m_bBassCancel = dAvg < m_rcBassCancel.th_on ? true : false;
	if (m_bBassCancel) {
		m_bBassLv2 = false;
		m_bBassLv4 = false;
		m_bBassLv6 = false;
	}

	// Treble Cancel
	dAvg = GetAvgHoleBrightness(frame, m_rcTrebleCancel);
	m_bTrebleCancel = dAvg < m_rcTrebleCancel.th_on ? true : false;
	if (m_bTrebleCancel) {
		m_bTrebleLv2 = false;
		m_bTrebleLv4 = false;
		m_bTrebleLv6 = false;
	}

	// ReRoll 
	dAvg = GetAvgHoleBrightness(frame, m_rcReRoll);
	// currently, nothing to do with re-roll

	// Bass Slow Crescendo
	dAvg = GetAvgHoleBrightness(frame, m_rcBassSlowCresc);
	if (dAvg < m_rcBassSlowCresc.th_on && !m_bBassSlowCresOn){
		m_bBassSlowCresOn = true;
	}
	else if (dAvg > m_rcBassSlowCresc.th_off && m_bBassSlowCresOn){
		m_bBassSlowCresOn = false;
	}

	// Treble Slow Crescendo
	dAvg = GetAvgHoleBrightness(frame, m_rcTrebleSlowCresc);
	if (dAvg < m_rcTrebleSlowCresc.th_on && !m_bTrebleSlowCresOn){
		m_bTrebleSlowCresOn = true;
	}
	else if (dAvg > m_rcTrebleSlowCresc.th_off && m_bTrebleSlowCresOn){
		m_bTrebleSlowCresOn = false;
	}

	// Bass Fast Crescendo
	dAvg = GetAvgHoleBrightness(frame, m_rcBassFastCresc);
	if (dAvg < m_rcBassFastCresc.th_on && !m_bBassFastCresOn){
		m_bBassFastCresOn = true;
	}
	else if (dAvg > m_rcBassFastCresc.th_off && m_bBassFastCresOn){
		m_bBassFastCresOn = false;
	}

	// Treble Fast Crescendo
	dAvg = GetAvgHoleBrightness(frame, m_rcTrebleFastCresc);
	if (dAvg < m_rcTrebleFastCresc.th_on && !m_bTrebleFastCresOn){
		m_bTrebleFastCresOn = true;
	}
	else if (dAvg > m_rcTrebleFastCresc.th_off && m_bTrebleFastCresOn){
		m_bTrebleFastCresOn = false;
	}

	// Bass Intensity 2->4->6
	for (UINT hole = 0; hole < 3; hole++) {
		dAvg = GetAvgHoleBrightness(frame, m_rcBassIntensity[hole]);
		if (dAvg < m_rcBassIntensity[hole].th_on) {
			switch (hole) {
			case 0:
				m_bBassLv2 = true;
				break;
			case 1:
				m_bBassLv4 = true;
				break;
			case 2:
				m_bBassLv6 = true;
				break;
			}
		}
	}

	// Treble Intensity 2->4->6
	for (UINT hole = 0; hole < 3; hole++) {
		dAvg = GetAvgHoleBrightness(frame, m_rcTrebleIntensity[hole]);
		if (dAvg < m_rcTrebleIntensity[hole].th_on) {
			switch (hole) {
			case 0:
				m_bTrebleLv2 = true;
				break;
			case 1:
				m_bTrebleLv4 = true;
				break;
			case 2:
				m_bTrebleLv6 = true;
				break;
			}
		}
	}

	if (!m_bEmulateOn){
		m_bBassLv2 = false;
		m_bBassLv4 = false;
		m_bBassLv6 = false;
		m_bTrebleLv2 = false;
		m_bTrebleLv4 = false;
		m_bTrebleLv6 = false;
		m_bBassSlowCresOn = false;
		m_bBassFastCresOn = false;
		m_bBassCancel = false;
		m_bTrebleSlowCresOn = false;
		m_bTrebleFastCresOn = false;
		m_bTrebleCancel = false;
	}
	
	// Draw Holes
	DrawHole(frame, m_rcBassCancel, m_bBassCancel);
	DrawHole(frame, m_rcTrebleCancel, m_bTrebleCancel);
	DrawHole(frame, m_rcBassSlowCresc, m_bBassSlowCresOn);
	DrawHole(frame, m_rcTrebleSlowCresc, m_bTrebleSlowCresOn);
	DrawHole(frame, m_rcBassFastCresc, m_bBassFastCresOn);
	DrawHole(frame, m_rcTrebleFastCresc, m_bTrebleFastCresOn);
	DrawHole(frame, m_rcBassIntensity[0], m_bBassLv2);
	DrawHole(frame, m_rcBassIntensity[1], m_bBassLv4);
	DrawHole(frame, m_rcBassIntensity[2], m_bBassLv6);
	DrawHole(frame, m_rcTrebleIntensity[0], m_bTrebleLv2);
	DrawHole(frame, m_rcTrebleIntensity[1], m_bTrebleLv4);
	DrawHole(frame, m_rcTrebleIntensity[2], m_bTrebleLv6);
	DrawHole(frame, m_rcReRoll, false);

	return;
}

void AmpicoA::CalcBassVelocity()
{
	static double dIntensityVelo = 0;

	// Intensity Operation
	BassIntensityCurv(dIntensityVelo);

	// Crescendo Operation
	static double dCresVelo = m_dBassMinVelo;
	BassCrescendoCurv(dCresVelo);

	m_iBassStackVelo = (int)(dIntensityVelo + dCresVelo - m_dBassMinVelo);

	if (m_iBassStackVelo > m_dBassMaxVelo){
		m_iBassStackVelo = (int)m_dBassMaxVelo;
	}
	else if (m_iBassStackVelo <  m_dBassMinVelo){
		m_iBassStackVelo = (int)m_dBassMinVelo;
	}

	return;
}


void AmpicoA::CalcTrebleVelocity()
{
	static double dIntensityVelo = 0;

	// Intensity Operation
	TrebleIntensityCurv(dIntensityVelo);

	// Crescendo Operation
	static double dCresVelo = m_dTrebleMinVelo;
	TrebleCrescendoCurv(dCresVelo);

	m_iTrebleStackVelo = (int)(dIntensityVelo + dCresVelo - m_dTrebleMinVelo);

	if (m_iTrebleStackVelo > m_dTrebleMaxVelo){
		m_iTrebleStackVelo = (int)m_dTrebleMaxVelo;
	}
	else if (m_iTrebleStackVelo <  m_dTrebleMinVelo){
		m_iTrebleStackVelo = (int)m_dTrebleMinVelo;
	}

	return;
}

void AmpicoA::BassIntensityCurv(double &dintensityVelo)
{

	const static double dVeloRange = m_dBassMaxVelo - m_dBassMinVelo;
	const double dIntensityStep = dVeloRange / (m_dFrameRate * m_dFullIntensityDelay); // 0 to 2-4-6 full intensity needs delay
	double dNewIntensityVelo = 0;

	// Intensity Operation
	if (m_bBassLv2 && m_bBassLv4 && m_bBassLv6){
		dNewIntensityVelo = m_dBassIntensity[6];
	}
	else if (m_bBassLv4 && m_bBassLv6){
		dNewIntensityVelo = m_dBassIntensity[5];
	}
	else if (m_bBassLv2 && m_bBassLv6){
		dNewIntensityVelo = m_dBassIntensity[4];
	}
	else if (m_bBassLv2 && m_bBassLv4 || m_bBassLv6){
		dNewIntensityVelo = m_dBassIntensity[3];
	}
	else if (m_bBassLv4){
		dNewIntensityVelo = m_dBassIntensity[2];
	}
	else if (m_bBassLv2){
		dNewIntensityVelo = m_dBassIntensity[1];
	}
	else{
		dNewIntensityVelo = m_dBassIntensity[0];
	}

	if (dintensityVelo < dNewIntensityVelo){
		dintensityVelo += dIntensityStep;
	}
	if (dintensityVelo > dNewIntensityVelo){
		dintensityVelo = dNewIntensityVelo;
	}

	return;
}


void AmpicoA::BassCrescendoCurv(double &dCresVelo)
{

	const static double dVeloRange = m_dBassMaxVelo - m_dBassMinVelo;

#ifdef _AMPICO_LINEAR_CRESCENDO

	// linear Curv
	const double dSlowCresStep = dVeloRange / (m_dFrameRate * m_dSlowCrescSec);	// slow crescendo 9sec
	const double dFastCresStep = dVeloRange / (m_dFrameRate * m_dFastCrescSec); // fast crescendo 2sec
	if (m_bBassSlowCresOn){
		// Crescendo
		dCresVelo += m_bBassFastCresOn ? dFastCresStep : dSlowCresStep;
	}
	else{
		// Decrescendo
		dCresVelo -= m_bBassFastCresOn ? dFastCresStep : dSlowCresStep;
	}

#else 
	// Cres Curv
	const static double dCurvRad = M_PI / 2; // =90deg
	if (m_bBassSlowCresOn){
		// Crescendo
		double dCurSinRad = asin((dCresVelo - m_dBassMinVelo) / dVeloRange);
		dCurSinRad += m_bBassFastCresOn ? (dCurvRad / (m_dFrameRate * m_dFastCrescSec)) : (dCurvRad / (m_dFrameRate * m_dSlowCrescSec));
		if (dCurSinRad > M_PI / 2){
			dCurSinRad = M_PI / 2;
		}
		// Sin Cresendo Curv sin(0 - pi/2)
		dCresVelo = m_dBassMinVelo + dVeloRange * sin(dCurSinRad);
	}
	else{
		// Decrescendo
		double dDecCosRad = acos((dCresVelo - m_dBassMaxVelo) / dVeloRange);
		dDecCosRad += m_bBassFastCresOn ? (dCurvRad / (m_dFrameRate * m_dFastCrescSec)) : (dCurvRad / (m_dFrameRate * m_dSlowCrescSec));
		if (dDecCosRad > M_PI){
			dDecCosRad = M_PI;
		}
		// Cos Cresendo Curv cos(pi/2 - pi)
		dCresVelo = m_dBassMaxVelo + dVeloRange * cos(dDecCosRad);
	}

#endif

	if (dCresVelo < m_dBassMinVelo){
		dCresVelo = m_dBassMinVelo;
	}
	else if (dCresVelo > m_dBassMaxVelo){
		dCresVelo = m_dBassMaxVelo;
	}

	return;
}

void AmpicoA::TrebleIntensityCurv(double &dintensityVelo)
{

	const static double dVeloRange = m_dTrebleMaxVelo - m_dTrebleMinVelo;
	const double dIntensityStep = dVeloRange / (m_dFrameRate * m_dFullIntensityDelay); // 0 to 2-4-6 full intensity needs delay

	double dNewIntensityVelo = 0;

	// Intensity Operation
	if (m_bTrebleLv2 && m_bTrebleLv4 && m_bTrebleLv6){
		dNewIntensityVelo = m_dTrebleIntensity[6];
	}
	else if (m_bTrebleLv4 && m_bTrebleLv6){
		dNewIntensityVelo = m_dTrebleIntensity[5];
	}
	else if (m_bTrebleLv2 && m_bTrebleLv6){
		dNewIntensityVelo = m_dTrebleIntensity[4];
	}
	else if (m_bTrebleLv2 && m_bTrebleLv4 || m_bTrebleLv6){
		dNewIntensityVelo = m_dTrebleIntensity[3];
	}
	else if (m_bTrebleLv4){
		dNewIntensityVelo = m_dTrebleIntensity[2];
	}
	else if (m_bTrebleLv2){
		dNewIntensityVelo = m_dTrebleIntensity[1];
	}
	else{
		dNewIntensityVelo = m_dTrebleIntensity[0];
	}

	if (dintensityVelo < dNewIntensityVelo){
		dintensityVelo += dIntensityStep;
	}
	if (dintensityVelo > dNewIntensityVelo){
		dintensityVelo = dNewIntensityVelo;
	}

	return;
}

void AmpicoA::TrebleCrescendoCurv(double &dCresVelo)
{
	const static double dVeloRange = m_dTrebleMaxVelo - m_dTrebleMinVelo;

#ifdef _AMPICO_LINEAR_CRESCENDO

	// linear Curv
	const double dSlowCresStep = dVeloRange / (m_dFrameRate * m_dSlowCrescSec);	// slow crescendo 9sec
	const double dFastCresStep = dVeloRange / (m_dFrameRate * m_dFastCrescSec); // fast crescendo 2sec
	if (m_bTrebleSlowCresOn){
		// Crescendo
		dCresVelo += m_bTrebleFastCresOn ? dFastCresStep : dSlowCresStep;
	}
	else{
		// Decrescendo
		dCresVelo -= m_bTrebleFastCresOn ? dFastCresStep : dSlowCresStep;
	}

#else 
	// Cres Curv
	const static double dCurvRad = M_PI / 2; // =90deg
	if (m_bTrebleSlowCresOn){
		// Crescendo
		double dCurSinRad = asin((dCresVelo - m_dTrebleMinVelo) / dVeloRange);
		dCurSinRad += m_bTrebleFastCresOn ? (dCurvRad / (m_dFrameRate * m_dFastCrescSec)) : (dCurvRad / (m_dFrameRate * m_dSlowCrescSec));
		if (dCurSinRad > M_PI / 2){
			dCurSinRad = M_PI / 2;
		}
		// Sin Cresendo Curv sin(0 - pi/2)
		dCresVelo = m_dTrebleMinVelo + dVeloRange * sin(dCurSinRad);
	}
	else{
		// Decrescendo
		double dDecCosRad = acos((dCresVelo - m_dTrebleMaxVelo) / dVeloRange);
		dDecCosRad += m_bTrebleFastCresOn ? (dCurvRad / (m_dFrameRate * m_dFastCrescSec)) : (dCurvRad / (m_dFrameRate * m_dSlowCrescSec));
		if (dDecCosRad > M_PI){
			dDecCosRad = M_PI;
		}
		// Cos Cresendo Curv cos(pi/2 - pi)
		dCresVelo = m_dTrebleMaxVelo + dVeloRange * cos(dDecCosRad);
	}

#endif

	if (dCresVelo < m_dTrebleMinVelo){
		dCresVelo = m_dTrebleMinVelo;
	}
	else if (dCresVelo > m_dTrebleMaxVelo){
		dCresVelo = m_dTrebleMaxVelo;
	}

	return;
}