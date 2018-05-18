#include "stdafx.h"
#include "AmpicoA.h"

#define _USE_MATH_DEFINES
#include <math.h>

//#define _AMPICO_LINEAR_CRESCENDO

AmpicoA::AmpicoA()
{
	m_BassSlowCres_x = 0;
	m_BassLv2_x = 0;
	m_BassLv4_x = 0;
	m_BassFastCres_x = 0;
	m_BassLv6_x = 0;
	m_BassCancel_x = 0;
	m_ReRoll_x = 0;
	m_TrebleCancel_x = 0;
	m_TrebleLv6_x = 0;
	m_TrebleFastCres_x = 0;
	m_TrebleLv4_x = 0;
	m_TrebleLv2_x = 0;
	m_TrebleSlowCres_x = 0;

	m_SlowCresHole_width = 0;
	m_SlowCresHole_height = 0;
	m_FastCresHole_width = 0;
	m_FastCresHole_height = 0;
	m_SusteinHole_width = 0;
	m_SusteinHole_height = 0;
	m_SoftHole_width = 0;
	m_SoftHole_height = 0;

	mSoftOnTH = 0;
	mSoftOffTH = 0;
	mSusuteinOnTH = 0;
	mSusuteinOffTH = 0;
	mIntensityTH = 0;

	for (int i = 0; i < 7; i++){
		m_BassIntensity[i] = 0;
		m_TrebleIntensity[i] = 0;
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

	m_iStackDevide = 43;
	m_iLowestNoteNo = 2;
	m_iHighestNoteNo = 84;
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
	char buf[256];
	std::ifstream ifs;

	ifs.open("Ampico_A.txt");
	if (ifs.fail()) return -1;
	ifs.getline(buf, sizeof(buf));
	while (buf[0] == '#'){
		ifs.getline(buf, sizeof(buf));
	}
	// Hole Size
	m_iNoteHoleWidth = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iNoteHoleHeigth = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_SusteinHole_width = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_SusteinHole_height = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_SoftHole_width = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_SoftHole_height = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_SlowCresHole_width = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_SlowCresHole_height = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_FastCresHole_width = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_FastCresHole_height = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));

	// Hole Open/Close TH
	m_iNoteOnTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iNoteOffTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	mSusuteinOnTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	mSusuteinOffTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	mSoftOnTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	mSoftOffTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	mIntensityTH = m_iNoteOnTH; // same TH with NoteOn

	// Bass Control Position
	m_BassSlowCres_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_BassLv2_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iSusteinPedalHoleX = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_BassLv4_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_BassFastCres_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_BassLv6_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_BassCancel_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));

	// Treble Control Position
	m_ReRoll_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_TrebleCancel_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_TrebleLv6_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_TrebleFastCres_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_TrebleLv4_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iSoftPedalHoleX = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_TrebleLv2_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_TrebleSlowCres_x = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));

	// Intensity 
	for (int i = 0; i < 7; ++i){
		m_BassIntensity[i] = atoi(buf);
		ifs.getline(buf, sizeof(buf));
	}
	ifs.getline(buf, sizeof(buf));
	for (int i = 0; i < 7; ++i){
		m_TrebleIntensity[i] = atoi(buf);
		ifs.getline(buf, sizeof(buf));
	}

	// Note Position
	for (int i = m_iLowestNoteNo; i <= m_iHighestNoteNo; ++i){
		ifs.getline(buf, sizeof(buf));
		m_iNote_x[i] = atoi(buf);
	}

	// Set Min/Max velocity
	m_iBassStackVelo = m_BassMinVelo = m_BassIntensity[0];
	m_BassMaxVelo = m_BassIntensity[6];
	m_iTrebleStackVelo = m_TrebleMinVelo = m_TrebleIntensity[0];
	m_TrebleMaxVelo = m_TrebleIntensity[6];

	ifs.close();

	m_iMinVelocity = (int)std::min(m_BassMinVelo, m_TrebleMinVelo);
	m_iMaxVelocity = (int)std::max(m_BassMaxVelo, m_TrebleMaxVelo);

	return 0;
}


int AmpicoA::Emulate(cv::Mat &frame, HDC &g_hdcImage, const HMIDIOUT &hm)
{

	// Send Midi Msg
	SendMidiMsg(hm);

	// Read Control Holes
	ReadExpressionHoles(frame, hm);

	// Calc Velocity
	CalcBassVelocity();
	CalcTrebleVelocity();

	static int BassVelDelay[MAXNoteOnFrames + 2] = { 0 };
	static int TrebleVelDelay[MAXNoteOnFrames + 2] = { 0 };
	BassVelDelay[0] = m_iBassStackVelo;
	TrebleVelDelay[0] = m_iTrebleStackVelo;
	m_iBassStackVelo = BassVelDelay[m_iNoteOnFrames + 1];
	m_iTrebleStackVelo = TrebleVelDelay[m_iNoteOnFrames + 1];

	for (int i = m_iNoteOnFrames + 1; i > 0; i--){
		int temp = BassVelDelay[i - 1];
		BassVelDelay[i] = temp;
		temp = TrebleVelDelay[i - 1];
		TrebleVelDelay[i] = temp;
	}


	// Scan Note Holes
	for (int n = m_iLowestNoteNo; n <= m_iHighestNoteNo; ++n) {

		double dAvg = 0;

		for (int y = 240; y < m_iNoteHoleHeigth + 240; y++){
			for (int x = m_iNote_x[n] + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_iNote_x[n] + m_iTrackingOffset; ++x){

				dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
			}
		}
		dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
		if (m_cNoteOn[n] == off && dAvg < m_iNoteOnTH && m_bEmulateOn)	{

			if (m_cNoteOnCnt[n] >= m_iNoteOnFrames){
				m_cNoteOnCnt[n] = 0;
				m_cNoteOn[n] = onTriger;
			}
			else{
				m_cNoteOnCnt[n]++;
			}
		}
		else if (m_cNoteOn[n] == on && dAvg > m_iNoteOffTH){

			m_cNoteOn[n] = offTriger;
		}
		if (m_cNoteOn[n] > 0 && m_bEmulateOn)
			cv::rectangle(frame, cv::Point(m_iNote_x[n] + m_iTrackingOffset, 240), cv::Point(m_iNote_x[n] + m_iNoteHoleHeigth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), cv::Scalar(0, 0, 200), 1, 1);
		else
			cv::rectangle(frame, cv::Point(m_iNote_x[n] + m_iTrackingOffset, 240), cv::Point(m_iNote_x[n] + m_iNoteHoleHeigth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), cv::Scalar(200, 0, 0), 1, 1);
	}

	// Draw Trackerbar
	cv::line(frame, cv::Point(3, 235), cv::Point(3, 245), cv::Scalar(200, 0, 200), 1, 4);
	cv::line(frame, cv::Point(637, 235), cv::Point(637, 245), cv::Scalar(200, 0, 200), 1, 4);
	cv::line(frame, cv::Point(0, 255), cv::Point(639, 255), cv::Scalar(100, 100, 0), 1, 4);
	cv::line(frame, cv::Point(0, 212), cv::Point(639, 212), cv::Scalar(100, 100, 0), 1, 4);

	mycv::cvtMat2HDC()(g_hdcImage, frame);
	return 0;
}


// Scan Intensity,Pedal Holes from Video Frame
int AmpicoA::ReadExpressionHoles(cv::Mat &frame, const HMIDIOUT &hm)
{
	double dAvg = 0;

	// Bass Cancel
	dAvg = 0;
	for (int y = 240; y < m_iNoteHoleHeigth + 240; y++){
		for (int x = m_BassCancel_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_BassCancel_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	m_bBassCancel = dAvg < mIntensityTH ? true : false;


	// Treble Cancel
	dAvg = 0;
	for (int y = 240; y < m_iNoteHoleHeigth + 240; y++){
		for (int x = m_TrebleCancel_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_TrebleCancel_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	m_bTrebleCancel = dAvg < mIntensityTH ? true : false;

	// Cancel Valve
	if (m_bBassCancel){
		m_bBassLv2 = false;
		m_bBassLv4 = false;
		m_bBassLv6 = false;
	}
	if (m_bTrebleCancel){
		m_bTrebleLv2 = false;
		m_bTrebleLv4 = false;
		m_bTrebleLv6 = false;
	}

	// Sustein Pedal 
	dAvg = 0;
	for (int y = 239; y < m_SusteinHole_height + 239; y++){
		for (int x = m_iSusteinPedalHoleX + m_iTrackingOffset; x < m_iSusteinPedalHoleX + m_SusteinHole_width + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_SusteinHole_height*m_SusteinHole_width;
	if (dAvg < mSusuteinOnTH && m_cSusteinPedalOn == off){
		m_cSusteinPedalOn = onTriger;
	}
	else if (dAvg > mSusuteinOffTH && m_cSusteinPedalOn == on){
		m_cSusteinPedalOn = offTriger;
	}

	// Soft Pedal 
	dAvg = 0;
	for (int y = 234; y < m_SoftHole_height + 234; y++){
		for (int x = m_iSoftPedalHoleX + m_iTrackingOffset; x < m_iSoftPedalHoleX + m_SoftHole_width + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_SoftHole_height*m_SoftHole_width;
	if (dAvg < mSoftOnTH && m_cSoftPedalOn == off){
		m_cSoftPedalOn = onTriger;
	}
	else if (dAvg > mSoftOffTH && m_cSoftPedalOn == on){
		m_cSoftPedalOn = offTriger;
	}

	// ReRoll 
	dAvg = 0;
	for (int y = 240; y < m_iNoteHoleHeigth + 240; y++){
		for (int x = m_ReRoll_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_ReRoll_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	if (dAvg < mIntensityTH){
		// Do ReRoll ...
	}

	// Bass Slow Crescendo
	dAvg = 0;
	for (int y = 234; y < m_SlowCresHole_height + 234; y++){
		for (int x = m_BassSlowCres_x + m_iTrackingOffset; x < m_BassSlowCres_x + m_SlowCresHole_width + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_SlowCresHole_height*m_SlowCresHole_width;
	if (dAvg < m_iNoteOnTH && !m_bBassSlowCresOn){
		m_bBassSlowCresOn = true;
	}
	else if (dAvg > m_iNoteOffTH && m_bBassSlowCresOn){
		m_bBassSlowCresOn = false;
	}

	// Treble Slow Crescendo
	dAvg = 0;
	for (int y = 234; y < m_SlowCresHole_height + 234; y++){
		for (int x = m_TrebleSlowCres_x + m_iTrackingOffset; x < m_TrebleSlowCres_x + m_SlowCresHole_width + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_SlowCresHole_height*m_SlowCresHole_width;
	if (dAvg < m_iNoteOnTH && !m_bTrebleSlowCresOn){
		m_bTrebleSlowCresOn = true;
	}
	else if (dAvg > m_iNoteOffTH && m_bTrebleSlowCresOn){
		m_bTrebleSlowCresOn = false;
	}

	// Bass Fast Crescendo
	dAvg = 0;
	for (int y = 238; y < m_FastCresHole_height + 238; y++){
		for (int x = m_BassFastCres_x + m_iTrackingOffset; x < m_BassFastCres_x + m_FastCresHole_width + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_FastCresHole_height*m_FastCresHole_width;
	if (dAvg < m_iNoteOnTH - 5 && !m_bBassFastCresOn){
		m_bBassFastCresOn = true;
	}
	else if (dAvg > m_iNoteOffTH - 5 && m_bBassFastCresOn){
		m_bBassFastCresOn = false;
	}

	// Treble Fast Crescendo
	dAvg = 0;
	for (int y = 238; y < m_FastCresHole_height + 238; y++){
		for (int x = m_TrebleFastCres_x + m_iTrackingOffset; x < m_TrebleFastCres_x + m_FastCresHole_width + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_FastCresHole_height*m_FastCresHole_width;
	if (dAvg < m_iNoteOnTH - 5 && !m_bTrebleFastCresOn){
		m_bTrebleFastCresOn = true;
	}
	else if (dAvg > m_iNoteOffTH - 5 && m_bTrebleFastCresOn){
		m_bTrebleFastCresOn = false;
	}

	const static int IntensityHoleY = 240;

	// Bass Lv2 Intensity 
	dAvg = 0;
	for (int y = IntensityHoleY; y < m_iNoteHoleHeigth + IntensityHoleY; y++){
		for (int x = m_BassLv2_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_BassLv2_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	if (dAvg < mIntensityTH){
		m_bBassLv2 = true;
	}

	// Bass Lv4 Intensity 
	dAvg = 0;
	for (int y = IntensityHoleY; y < m_iNoteHoleHeigth + IntensityHoleY; y++){
		for (int x = m_BassLv4_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_BassLv4_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	if (dAvg < mIntensityTH){
		m_bBassLv4 = true;
	}
	// Bass Lv6 Intensity 
	dAvg = 0;
	for (int y = IntensityHoleY; y < m_iNoteHoleHeigth + IntensityHoleY; y++){
		for (int x = m_BassLv6_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_BassLv6_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	if (dAvg < mIntensityTH){
		m_bBassLv6 = true;
	}

	// Treble Lv2 Intensity 
	dAvg = 0;
	for (int y = IntensityHoleY; y < m_iNoteHoleHeigth + IntensityHoleY; y++){
		for (int x = m_TrebleLv2_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_TrebleLv2_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	if (dAvg < mIntensityTH){
		m_bTrebleLv2 = true;
	}

	// Treble Lv4 Intensity 
	dAvg = 0;
	for (int y = IntensityHoleY; y < m_iNoteHoleHeigth + IntensityHoleY; y++){
		for (int x = m_TrebleLv4_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_TrebleLv4_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	if (dAvg < mIntensityTH){
		m_bTrebleLv4 = true;
	}

	// Treble Lv6 Intensity 
	dAvg = 0;
	for (int y = IntensityHoleY; y < m_iNoteHoleHeigth + IntensityHoleY; y++){
		for (int x = m_TrebleLv6_x + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_TrebleLv6_x + m_iTrackingOffset; ++x){
			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iNoteHoleWidth*m_iNoteHoleHeigth;
	if (dAvg < mIntensityTH){
		m_bTrebleLv6 = true;
	}

	for (int i = 0; i < 5; i++){

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
		m_cSusteinPedalOn = offTriger;
		m_cSoftPedalOn = offTriger;
	}


	// Draw Holes
	cv::Scalar scr;
	cv::Scalar scrOn(0, 0, 200);
	cv::Scalar scrOff(200, 0, 0);

	// Sustein Pedal
	scr = (m_cSusteinPedalOn > 0) ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_iSusteinPedalHoleX + m_iTrackingOffset, 239), cv::Point(m_iSusteinPedalHoleX + m_SusteinHole_width - 1 + m_iTrackingOffset, 239 + m_SusteinHole_height - 1), scr, 1, 1);
	// Soft Pedal
	scr = (m_cSoftPedalOn > 0) ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_iSoftPedalHoleX + m_iTrackingOffset, 234), cv::Point(m_iSoftPedalHoleX + m_SoftHole_width - 1 + m_iTrackingOffset, 234 + m_SoftHole_height - 1), scr, 1, 1);
	// ReRoll Hole
	//
	scr = scrOff;
	cv::rectangle(frame, cv::Point(m_ReRoll_x + m_iTrackingOffset, 240), cv::Point(m_ReRoll_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);
	// Bass Slow Cres Hole
	scr = m_bBassSlowCresOn ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_BassSlowCres_x + m_iTrackingOffset, 234), cv::Point(m_BassSlowCres_x + m_SlowCresHole_width - 1 + m_iTrackingOffset, 234 + m_SlowCresHole_height - 1), scr, 1, 1);
	// Bass Fast Cres Hole
	scr = m_bBassFastCresOn ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_BassFastCres_x + m_iTrackingOffset, 238), cv::Point(m_BassFastCres_x + m_FastCresHole_width - 1 + m_iTrackingOffset, 238 + m_FastCresHole_height - 1), scr, 1, 1);
	// Bass Lv2 Hole
	scr = m_bBassLv2 ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_BassLv2_x + m_iTrackingOffset, 240), cv::Point(m_BassLv2_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);
	// Bass Lv4 Hole
	scr = m_bBassLv4 ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_BassLv4_x + m_iTrackingOffset, 240), cv::Point(m_BassLv4_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);
	// Bass Lv6 Hole
	scr = m_bBassLv6 ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_BassLv6_x + m_iTrackingOffset, 240), cv::Point(m_BassLv6_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);
	// Bass Cancel Hole
	scr = m_bBassCancel ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_BassCancel_x + m_iTrackingOffset, 240), cv::Point(m_BassCancel_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);
	// Treble Slow Cres Hole
	scr = m_bTrebleSlowCresOn ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_TrebleSlowCres_x + m_iTrackingOffset, 234), cv::Point(m_TrebleSlowCres_x + m_SlowCresHole_width - 1 + m_iTrackingOffset, 234 + m_SlowCresHole_height - 1), scr, 1, 1);
	// Treble Fast Cres Hole
	scr = m_bTrebleFastCresOn ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_TrebleFastCres_x + m_iTrackingOffset, 238), cv::Point(m_TrebleFastCres_x + m_FastCresHole_width - 1 + m_iTrackingOffset, 238 + m_FastCresHole_height - 1), scr, 1, 1);
	// Treble Lv2 Hole
	scr = m_bTrebleLv2 ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_TrebleLv2_x + m_iTrackingOffset, 240), cv::Point(m_TrebleLv2_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);
	// Treble Lv4 Hole
	scr = m_bTrebleLv4 ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_TrebleLv4_x + m_iTrackingOffset, 240), cv::Point(m_TrebleLv4_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);
	// Treble Lv6 Hole
	scr = m_bTrebleLv6 ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_TrebleLv6_x + m_iTrackingOffset, 240), cv::Point(m_TrebleLv6_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);
	// Treble Cancel Hole
	scr = m_bTrebleCancel ? scrOn : scrOff;
	cv::rectangle(frame, cv::Point(m_TrebleCancel_x + m_iTrackingOffset, 240), cv::Point(m_TrebleCancel_x + m_iNoteHoleWidth - 1 + m_iTrackingOffset, 240 + m_iNoteHoleHeigth - 1), scr, 1, 1);

	return 0;
}

int AmpicoA::CalcBassVelocity()
{
	static double intensityVelo = 0;

	// Intensity Operation
	BassIntensityCurv(intensityVelo);

	// Crescendo Operation
	static double dCresVelo = m_BassMinVelo;
	BassCrescendoCurv(dCresVelo);

	m_iBassStackVelo = intensityVelo + (dCresVelo - m_BassMinVelo);

	if (m_iBassStackVelo > m_BassMaxVelo){
		m_iBassStackVelo = (int)m_BassMaxVelo;
	}
	else if (m_iBassStackVelo <  m_BassMinVelo){
		m_iBassStackVelo = (int)m_BassMinVelo;
	}

	return 0;
}


int AmpicoA::CalcTrebleVelocity()
{
	static double intensityVelo = 0;

	// Intensity Operation
	TrebleIntensityCurv(intensityVelo);

	// Crescendo Operation
	static double dCresVelo = m_TrebleMinVelo;
	TrebleCrescendoCurv(dCresVelo);

	m_iTrebleStackVelo = intensityVelo + (dCresVelo - m_TrebleMinVelo);

	if (m_iTrebleStackVelo > m_TrebleMaxVelo){
		m_iTrebleStackVelo = (int)m_TrebleMaxVelo;
	}
	else if (m_iTrebleStackVelo <  m_TrebleMinVelo){
		m_iTrebleStackVelo = (int)m_TrebleMinVelo;
	}

	return 0;
}

int AmpicoA::BassIntensityCurv(double &dintensityVelo)
{

	const static double dVeloRange = m_BassMaxVelo - m_BassMinVelo;
	const double dIntensityStep = dVeloRange / (m_dFrameRate * 0.15); // 0 to 2-4-6 full intensity needs 0.15sec

	double newintensityVelo = 0;

	// Intensity Operation
	if (m_bBassLv2 && m_bBassLv4 && m_bBassLv6){
		newintensityVelo = m_BassIntensity[6];
	}
	else if (m_bBassLv4 && m_bBassLv6){
		newintensityVelo = m_BassIntensity[5];
	}
	else if (m_bBassLv2 && m_bBassLv6){
		newintensityVelo = m_BassIntensity[4];
	}
	else if (m_bBassLv2 && m_bBassLv4 || m_bBassLv6){
		newintensityVelo = m_BassIntensity[3];
	}
	else if (m_bBassLv4){
		newintensityVelo = m_BassIntensity[2];
	}
	else if (m_bBassLv2){
		newintensityVelo = m_BassIntensity[1];
	}
	else{
		newintensityVelo = m_BassIntensity[0];
	}

	if (dintensityVelo < newintensityVelo){
		dintensityVelo += dIntensityStep;
	}
	if (dintensityVelo > newintensityVelo){
		dintensityVelo = newintensityVelo;
	}

	return 0;
}


int AmpicoA::BassCrescendoCurv(double &dCresVelo)
{

	const static double dVeloRange = m_BassMaxVelo - m_BassMinVelo;

#ifdef _AMPICO_LINEAR_CRESCENDO

	// linear Curv
	const double dSlowCresStep = dVeloRange / (m_dFrameRate * 9);	// slow crescendo 9sec
	const double dFastCresStep = dVeloRange / (m_dFrameRate * 2); // fast crescendo 2sec
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
		double dCurSinRad = asin((dCresVelo - m_BassMinVelo) / dVeloRange);
		dCurSinRad += m_bBassFastCresOn ? (dCurvRad / (m_dFrameRate * 2)) : (dCurvRad / (m_dFrameRate * 9));
		if (dCurSinRad > M_PI / 2){
			dCurSinRad = M_PI / 2;
		}
		// Sin Cresendo Curv sin(0 - pi/2)
		dCresVelo = m_BassMinVelo + dVeloRange * sin(dCurSinRad);
	}
	else{
		// Decrescendo
		double dDecCosRad = acos((dCresVelo - m_BassMaxVelo) / dVeloRange);
		dDecCosRad += m_bBassFastCresOn ? (dCurvRad / (m_dFrameRate * 2)) : (dCurvRad / (m_dFrameRate * 9));
		if (dDecCosRad > M_PI){
			dDecCosRad = M_PI;
		}
		// Cos Cresendo Curv cos(pi/2 - pi)
		dCresVelo = m_BassMaxVelo + dVeloRange * cos(dDecCosRad);
	}

#endif

	if (dCresVelo < m_BassMinVelo){
		dCresVelo = m_BassMinVelo;
	}
	else if (dCresVelo > m_BassMaxVelo){
		dCresVelo = m_BassMaxVelo;
	}

	return 0;
}

int AmpicoA::TrebleIntensityCurv(double &dintensityVelo)
{

	const static double dVeloRange = m_TrebleMaxVelo - m_TrebleMinVelo;
	const double dIntensityStep = dVeloRange / (m_dFrameRate * 0.15); // 0 to 2-4-6 full intensity needs 0.15sec

	double newintensityVelo = 0;

	// Intensity Operation
	if (m_bTrebleLv2 && m_bTrebleLv4 && m_bTrebleLv6){
		newintensityVelo = m_TrebleIntensity[6];
	}
	else if (m_bTrebleLv4 && m_bTrebleLv6){
		newintensityVelo = m_TrebleIntensity[5];
	}
	else if (m_bTrebleLv2 && m_bTrebleLv6){
		newintensityVelo = m_TrebleIntensity[4];
	}
	else if (m_bTrebleLv2 && m_bTrebleLv4 || m_bTrebleLv6){
		newintensityVelo = m_TrebleIntensity[3];
	}
	else if (m_bTrebleLv4){
		newintensityVelo = m_TrebleIntensity[2];
	}
	else if (m_bTrebleLv2){
		newintensityVelo = m_TrebleIntensity[1];
	}
	else{
		newintensityVelo = m_TrebleIntensity[0];
	}

	if (dintensityVelo < newintensityVelo){
		dintensityVelo += dIntensityStep;
	}
	if (dintensityVelo > newintensityVelo){
		dintensityVelo = newintensityVelo;
	}

	return 0;
}

int AmpicoA::TrebleCrescendoCurv(double &dCresVelo)
{
	const static double dVeloRange = m_TrebleMaxVelo - m_TrebleMinVelo;

#ifdef _AMPICO_LINEAR_CRESCENDO

	// linear Curv
	const double dSlowCresStep = dVeloRange / (m_dFrameRate * 9);	// slow crescendo 9sec
	const double dFastCresStep = dVeloRange / (m_dFrameRate * 2); // fast crescendo 2sec
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
		double dCurSinRad = asin((dCresVelo - m_TrebleMinVelo) / dVeloRange);
		dCurSinRad += m_bTrebleFastCresOn ? (dCurvRad / (m_dFrameRate * 2)) : (dCurvRad / (m_dFrameRate * 9));
		if (dCurSinRad > M_PI / 2){
			dCurSinRad = M_PI / 2;
		}
		// Sin Cresendo Curv sin(0 - pi/2)
		dCresVelo = m_TrebleMinVelo + dVeloRange * sin(dCurSinRad);
	}
	else{
		// Decrescendo
		double dDecCosRad = acos((dCresVelo - m_TrebleMaxVelo) / dVeloRange);
		dDecCosRad += m_bTrebleFastCresOn ? (dCurvRad / (m_dFrameRate * 2)) : (dCurvRad / (m_dFrameRate * 9));
		if (dDecCosRad > M_PI){
			dDecCosRad = M_PI;
		}
		// Cos Cresendo Curv cos(pi/2 - pi)
		dCresVelo = m_TrebleMaxVelo + dVeloRange * cos(dDecCosRad);
	}

#endif

	if (dCresVelo < m_TrebleMinVelo){
		dCresVelo = m_TrebleMinVelo;
	}
	else if (dCresVelo > m_TrebleMaxVelo){
		dCresVelo = m_TrebleMaxVelo;
	}

	return 0;
}