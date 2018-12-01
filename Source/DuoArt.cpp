
#include "stdafx.h"
#include "Player.h"
#include "DuoArt.h"



DuoArt::DuoArt()
{ 
	m_bBassAccent = false;
	m_bTrebleAccent = false;
	m_iBassAccentDelayCnt = 0;
	m_iTrebleAccentDelayCnt = 0;
	m_iAccentDelayFrames = 1; 
	m_dAccompVelo = 0;
	m_dThemeVelo = 0;
	m_dTheme1 = 0;
	m_dTheme2 = 0;
	m_dTheme4 = 0;
	m_dTheme8 = 0;
	m_dAccomp1 = 0;
	m_dAccomp2 = 0;
	m_dAccomp4 = 0;
	m_dAccomp8 = 0;
	m_iStackDevide = 44;
	m_iLowestNoteNo = 4;
	m_iHighestNoteNo = 83;
}



int DuoArt::LoadPlayerSettings()
{
	char buf[256];
	std::ifstream ifs;

	ifs.open("Duo-Art.txt");
	if (ifs.fail()) return -1;
	ifs.getline(buf, sizeof(buf));
	while (buf[0] == '#'){
		ifs.getline(buf, sizeof(buf));
	}
	m_iNoteOnTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iNoteOffTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iNoteHoleWidth = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iNoteHoleHeigth = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iPedalHoleWidth = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iPedalHoleHeight = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iPedalOnTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iPedalOffTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iSusteinPedalHoleX = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iSoftPedalHoleX = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iSnakeHoleTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iBassSnakebiteX = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iTrebleSnakebiteX = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iSnakeHoleWidth = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iSnakeHoleHeight = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iDAHoleTH = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iDAHoleWidth = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iDAHoleHeight = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	for (int i = 0; i < 4; ++i){
		ifs.getline(buf, sizeof(buf));
		m_iAccompHoleX[i] = atoi(buf);
	}
	ifs.getline(buf, sizeof(buf));
	for (int i = 0; i < 4; ++i){
		ifs.getline(buf, sizeof(buf));
		m_iThemeHoleX[i] = atoi(buf);
	}
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iMinVelocity = m_iAccompMinVelo = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	m_iAccompMaxVelo = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	ifs.getline(buf, sizeof(buf));
	m_iThemeMinVelo = atoi(buf);
	ifs.getline(buf, sizeof(buf));
	m_iMaxVelocity = m_iThemeMaxVelo = atoi(buf);
	ifs.getline(buf, sizeof(buf));

	for (int i = 4; i < KeyNum - 4; ++i){
		ifs.getline(buf, sizeof(buf));
		m_iNote_x[i] = atoi(buf);
	}

	ifs.close();

	//set default velocity
	m_iBassStackVelo = m_iTrebleStackVelo = m_iAccompMinVelo;
	m_iPrevBassStackVelo = m_iPrevBassStackVelo = m_iAccompMinVelo;

	return 0;
}


int DuoArt::Emulate(cv::Mat &frame, HDC &g_hdcImage, const HMIDIOUT &hm){

	// Send Midi Msg to Midi Device
	SendMidiMsg(hm);

	double dAvg = 0;

	//Duo-Art Accomp Holes check(Accomp lv.1->lv.8)
	for (int n = 0; n < 4; ++n){
		dAvg = 0;
		for (int y = 223; y < m_iDAHoleHeight + 223; y++){
			for (int x = m_iAccompHoleX[n] + m_iTrackingOffset; x < m_iAccompHoleX[n] + m_iDAHoleWidth + m_iTrackingOffset; ++x){

				// Calc Avg Brightness
				dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3]; // Blue Channel
			}
		}
		bool bAccompOn = false;
		dAvg /= m_iDAHoleWidth*m_iDAHoleHeight;
		if (dAvg < m_iDAHoleTH&&m_bEmulateOn)	{
			cv::rectangle(frame, cv::Point(m_iAccompHoleX[n] + m_iTrackingOffset, 223), cv::Point(m_iAccompHoleX[n] + m_iDAHoleWidth - 1 + m_iTrackingOffset, 223 + m_iDAHoleHeight - 1), cv::Scalar(0, 0, 200), 1, 1);
			bAccompOn = true;
		}
		else {
			cv::rectangle(frame, cv::Point(m_iAccompHoleX[n] + m_iTrackingOffset, 223), cv::Point(m_iAccompHoleX[n] + m_iDAHoleWidth - 1 + m_iTrackingOffset, 223 + m_iDAHoleHeight - 1), cv::Scalar(200, 0, 0), 1, 1);
			bAccompOn = false;
		}
		switch (n) {
		case 0:
			Accomp1(bAccompOn);
			break;
		case 1:
			Accomp2(bAccompOn);
			break;
		case 2:
			Accomp4(bAccompOn);
			break;
		case 3:
			Accomp8(bAccompOn);
			break;
		}
	}

	// Calc Accomp Velocity
	m_dAccompVelo = m_iAccompMinVelo + (m_dAccomp1 + m_dAccomp2 + m_dAccomp4 + m_dAccomp8)*((m_iAccompMaxVelo - m_iAccompMinVelo) / 15.0);



	// Check Duo-Art Theme Hole(Accomp lv.8->lv.1)
	for (int n = 0; n < 4; ++n){
		dAvg = 0;
		for (int y = 223; y < m_iDAHoleHeight + 223; y++){
			for (int x = m_iThemeHoleX[n] + m_iTrackingOffset; x < m_iThemeHoleX[n] + m_iDAHoleWidth + m_iTrackingOffset; ++x){

				dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
			}
		}
		bool bThemeOn = false;
		dAvg /= m_iDAHoleWidth*m_iDAHoleHeight;
		if (dAvg < m_iDAHoleTH&&m_bEmulateOn)	{
			cv::rectangle(frame, cv::Point(m_iThemeHoleX[n] + m_iTrackingOffset, 223), cv::Point(m_iThemeHoleX[n] + m_iDAHoleWidth - 1 + m_iTrackingOffset, 223 + m_iDAHoleHeight - 1), cv::Scalar(0, 0, 200), 1, 1);
			bThemeOn = true;
		}
		else {
			cv::rectangle(frame, cv::Point(m_iThemeHoleX[n] + m_iTrackingOffset, 223), cv::Point(m_iThemeHoleX[n] + m_iDAHoleWidth - 1 + m_iTrackingOffset, 223 + m_iDAHoleHeight - 1), cv::Scalar(200, 0, 0), 1, 1);
			bThemeOn = false;
		}
		switch (n) {
		case 0:
			Theme8(bThemeOn);
			break;
		case 1:
			Theme4(bThemeOn);
			break;
		case 2:
			Theme2(bThemeOn);
			break;
		case 3:
			Theme1(bThemeOn);
			break;
		}
	}

	// Calc Theme Velocity
	m_dThemeVelo = m_iThemeMinVelo + (m_dTheme1 + m_dTheme2 + m_dTheme4 + m_dTheme8)*((m_iThemeMaxVelo - m_iThemeMinVelo) / 15.0);



	// Check Bass Snakebite
	dAvg = 0;
	for (int y = 239; y < m_iSnakeHoleHeight + 239; y++){
		for (int x = m_iBassSnakebiteX + m_iTrackingOffset; x < m_iBassSnakebiteX + m_iSnakeHoleWidth + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iSnakeHoleHeight*m_iSnakeHoleWidth;
	if ((dAvg < m_iSnakeHoleTH&&m_bEmulateOn)|| m_iBassAccentDelayCnt >0){
		if (dAvg < m_iSnakeHoleTH&&m_bEmulateOn) m_iBassAccentDelayCnt = 3;
		cv::rectangle(frame, cv::Point(m_iBassSnakebiteX + m_iTrackingOffset, 239), cv::Point(m_iBassSnakebiteX + m_iSnakeHoleWidth - 1 + m_iTrackingOffset, 239 + m_iSnakeHoleHeight - 1), cv::Scalar(0, 0, 200), 1, 1);
		m_bBassAccent = true;
	}
	else {
		cv::rectangle(frame, cv::Point(m_iBassSnakebiteX + m_iTrackingOffset, 239), cv::Point(m_iBassSnakebiteX + m_iSnakeHoleWidth - 1 + m_iTrackingOffset, 239 + m_iSnakeHoleHeight - 1), cv::Scalar(200, 0, 0), 1, 1);
		m_bBassAccent = false;
	}
	if (m_iBassAccentDelayCnt >= 0)	m_iBassAccentDelayCnt--;


	// Check Treble Snakebite
	dAvg = 0;
	for (int y = 239; y < m_iSnakeHoleHeight + 239; y++){
		for (int x = m_iTrebleSnakebiteX + m_iTrackingOffset; x < m_iTrebleSnakebiteX + m_iSnakeHoleWidth + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iSnakeHoleHeight*m_iSnakeHoleWidth;
	if ((dAvg < m_iSnakeHoleTH&&m_bEmulateOn) || m_iTrebleAccentDelayCnt >0)	{
		if (dAvg < m_iSnakeHoleTH&&m_bEmulateOn)	m_iTrebleAccentDelayCnt = 3;
		cv::rectangle(frame, cv::Point(m_iTrebleSnakebiteX + m_iTrackingOffset, 239), cv::Point(m_iTrebleSnakebiteX + m_iSnakeHoleWidth - 1 + m_iTrackingOffset, 239 + m_iSnakeHoleHeight - 1), cv::Scalar(0, 0, 200), 1, 1);
		m_bTrebleAccent = true;
	}
	else {
		cv::rectangle(frame, cv::Point(m_iTrebleSnakebiteX + m_iTrackingOffset, 239), cv::Point(m_iTrebleSnakebiteX + m_iSnakeHoleWidth - 1 + m_iTrackingOffset, 239 + m_iSnakeHoleHeight - 1), cv::Scalar(200, 0, 0), 1, 1);
		m_bTrebleAccent = false;
	}
	if (m_iTrebleAccentDelayCnt >= 0)	m_iTrebleAccentDelayCnt--;

	
	// Check Sustein Pedal
	dAvg = 0;
	for (int y = 235; y < m_iPedalHoleHeight + 235; y++){
		for (int x = m_iSusteinPedalHoleX + m_iTrackingOffset; x < m_iSusteinPedalHoleX + m_iPedalHoleWidth + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iPedalHoleHeight*m_iPedalHoleWidth;
	if (dAvg < m_iPedalOnTH && m_cSusteinPedalOn == off && m_bEmulateOn)	{
		m_cSusteinPedalOn = onTriger;
	}
	else if (dAvg > m_iPedalOffTH && m_cSusteinPedalOn == on) {
		m_cSusteinPedalOn = offTriger;
	}

	if (m_cSusteinPedalOn > 0 && m_bEmulateOn)
		cv::rectangle(frame, cv::Point(m_iSusteinPedalHoleX + m_iTrackingOffset, 235), cv::Point(m_iSusteinPedalHoleX + m_iPedalHoleWidth - 1 + m_iTrackingOffset, 235 + m_iPedalHoleHeight - 1), cv::Scalar(0, 0, 200), 1, 1);
	else
		cv::rectangle(frame, cv::Point(m_iSusteinPedalHoleX + m_iTrackingOffset, 235), cv::Point(m_iSusteinPedalHoleX + m_iPedalHoleWidth - 1 + m_iTrackingOffset, 235 + m_iPedalHoleHeight - 1), cv::Scalar(200, 0, 0), 1, 1);


	// Check Soft Pedal
	dAvg = 0;
	for (int y = 235; y < m_iPedalHoleHeight + 235; y++){
		for (int x = m_iSoftPedalHoleX + m_iTrackingOffset; x < m_iSoftPedalHoleX + m_iPedalHoleWidth + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iPedalHoleHeight*m_iPedalHoleWidth;
	if (dAvg < m_iPedalOnTH && m_cSoftPedalOn == off && m_bEmulateOn)	{
		m_cSoftPedalOn = onTriger;
	}
	else if (dAvg > m_iPedalOffTH&&m_cSoftPedalOn == on){
		m_cSoftPedalOn = offTriger;
	}

	if (m_cSoftPedalOn > 0 && m_bEmulateOn)
		cv::rectangle(frame, cv::Point(m_iSoftPedalHoleX + m_iTrackingOffset, 237), cv::Point(m_iSoftPedalHoleX + m_iPedalHoleWidth - 1 + m_iTrackingOffset, 237 + m_iPedalHoleHeight - 1), cv::Scalar(0, 0, 200), 1, 1);
	else
		cv::rectangle(frame, cv::Point(m_iSoftPedalHoleX + m_iTrackingOffset, 237), cv::Point(m_iSoftPedalHoleX + m_iPedalHoleWidth - 1 + m_iTrackingOffset, 237 + m_iPedalHoleHeight - 1), cv::Scalar(200, 0, 0), 1, 1);


	// Calc Bass Stack Velocity
	if (m_bBassAccent){
		if (m_iPrevBassStackVelo < m_dThemeVelo){
			m_iBassStackVelo += ((m_dThemeVelo - m_iPrevBassStackVelo) / (double)m_iAccentDelayFrames);
		}
	}
	else{
		if (m_iPrevBassStackVelo > m_dAccompVelo){
			m_iBassStackVelo -= (m_iPrevBassStackVelo - m_dAccompVelo) / (double)m_iAccentDelayFrames;
		}
		else{

			m_iBassStackVelo = (int)m_dAccompVelo;
		}
	}

	// Calc Treble Stack Velocity
	if (m_bTrebleAccent){
		if (m_iPrevTrebleStackVelo < m_dThemeVelo){
			m_iTrebleStackVelo +=((m_dThemeVelo - m_iPrevTrebleStackVelo) / (double)m_iAccentDelayFrames);
		}
	}
	else{
		if (m_iPrevTrebleStackVelo > m_dAccompVelo){
			m_iTrebleStackVelo -= (m_iPrevTrebleStackVelo -m_dAccompVelo) / (double)m_iAccentDelayFrames;
		}
		else{
			m_iTrebleStackVelo = (int)m_dAccompVelo;
		}
	}

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

	m_iPrevBassStackVelo = m_iBassStackVelo;
	m_iPrevTrebleStackVelo = m_iTrebleStackVelo;

	//checks the notes are on or off

	for (int n = m_iLowestNoteNo; n <= m_iHighestNoteNo; ++n){

		dAvg = 0;
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

