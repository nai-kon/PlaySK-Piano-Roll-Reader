
#include "stdafx.h"
#include "Player.h"


Player::Player()
{
	// Init
	m_iSusteinPedalHoleX = m_iSoftPedalHoleX = 0;
	m_iNoteHoleWidth = m_iNoteHoleHeigth = 0;
	m_iPedalHoleWidth = m_iPedalHoleHeight = 0;

	m_iLowestNoteNo = 0;
	m_iHighestNoteNo = 87;
	m_iStackDevide = 43; // Bass:0-43 Treble:44-87
	
	for (int i = 0; i < KeyNum; ++i){
		m_iNote_x[i] = 0;
		m_cNoteOn[i] = off;
		m_cNoteOnCnt[i] = 0;
	}

	m_cSusteinPedalOn = m_cSoftPedalOn = off;
	m_iNoteOnTH = m_iNoteOffTH = 0;
	m_iPedalOnTH = m_iPedalOffTH = 0;
	m_iTrackingOffset = 0;
	m_iNoteOnFrames = 0;
	m_dFrameRate = 0;
	m_iMinVelocity = m_iMaxVelocity = m_iBassStackVelo = m_iTrebleStackVelo = 70;

	m_bEmulateOn = false;
}

Player::~Player()
{

}

int Player::NoteAllOff(const HMIDIOUT &hm)
{

	m_cSoftPedalOn = offTriger;
	m_cSusteinPedalOn = offTriger;
	for (int i = 0; i < KeyNum; ++i) {
		m_cNoteOn[i] = offTriger;
		m_cNoteOnCnt[i] = 0;
	}

	SendMidiMsg(hm);

	return 0;
}

int Player::Emulate(cv::Mat &frame, HDC &g_hdcImage,const HMIDIOUT &hm)
{

	// Send Midi Msg to Midi Device
	SendMidiMsg(hm);

	// Check Sustein Pedal Hole
	double dAvg = 0;
	for (int y = 237; y < m_iPedalHoleHeight + 237; y++){
		for (int x = m_iSusteinPedalHoleX + m_iTrackingOffset; x < m_iSusteinPedalHoleX + m_iPedalHoleWidth + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];  // Blue Channel
		}
	}
	// Calc Avg Brightness
	dAvg /= m_iPedalHoleHeight*m_iPedalHoleWidth;

	if (dAvg < m_iPedalOnTH && m_cSusteinPedalOn == off && m_bEmulateOn)	{
		m_cSusteinPedalOn = onTriger;
	}
	else if (dAvg > m_iPedalOffTH && m_cSusteinPedalOn == on) {
		m_cSusteinPedalOn = offTriger;
	}

	if (m_cSusteinPedalOn > 0 && m_bEmulateOn)
		cv::rectangle(frame, cv::Point(m_iSusteinPedalHoleX + m_iTrackingOffset, 237), cv::Point(m_iSusteinPedalHoleX + m_iPedalHoleWidth - 1 + m_iTrackingOffset, 237 + m_iPedalHoleHeight - 1), cv::Scalar(0, 0, 200), 1, 1);
	else
		cv::rectangle(frame, cv::Point(m_iSusteinPedalHoleX + m_iTrackingOffset, 237), cv::Point(m_iSusteinPedalHoleX + m_iPedalHoleWidth - 1 + m_iTrackingOffset, 237 + m_iPedalHoleHeight - 1), cv::Scalar(200, 0, 0), 1, 1);



	// Check Soft Pedal Hole
	dAvg = 0;
	for (int y = 237; y < m_iPedalHoleHeight + 237; y++){
		for (int x = m_iSoftPedalHoleX + m_iTrackingOffset; x < m_iSoftPedalHoleX + m_iPedalHoleWidth + m_iTrackingOffset; ++x){

			dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
		}
	}
	dAvg /= m_iPedalHoleHeight*m_iPedalHoleWidth;
	if (dAvg < m_iPedalOnTH && m_cSoftPedalOn == off && m_bEmulateOn)	{
		m_cSoftPedalOn = onTriger;
	}
	else if (dAvg > m_iPedalOffTH && m_cSoftPedalOn == on){
		m_cSoftPedalOn = offTriger;
	}

	if (m_cSoftPedalOn > 0 && m_bEmulateOn)
		cv::rectangle(frame, cv::Point(m_iSoftPedalHoleX + m_iTrackingOffset, 237), cv::Point(m_iSoftPedalHoleX + m_iPedalHoleWidth - 1 + m_iTrackingOffset, 237 + m_iPedalHoleHeight - 1), cv::Scalar(0, 0, 200), 1, 1);
	else
		cv::rectangle(frame, cv::Point(m_iSoftPedalHoleX + m_iTrackingOffset, 237), cv::Point(m_iSoftPedalHoleX + m_iPedalHoleWidth - 1 + m_iTrackingOffset, 237 + m_iPedalHoleHeight - 1), cv::Scalar(200, 0, 0), 1, 1);


	// Check Reroll Hole
	//dAvg = 0;
	//for (int y = 237; y < 8 + 237; y++){
	//	for (int x = 17 + m_iTrackingOffset; x < 22 + m_iTrackingOffset; ++x){
	//		dAvg += frame.data[y * VIDEO_WIDTH * 3 + x * 3];
	//	}
	//}
	//cv::rectangle(frame, cv::Point(17 + m_iTrackingOffset, 237), cv::Point(22 - 1 + m_iTrackingOffset, 237 + 8 - 1), cv::Scalar(200, 0, 0), 1, 1);
	//dAvg /= 8 * 5;
	//if (dAvg<m_iNoteOnTH) {
	//	tracking = false;
	//	m_bEmulateOn = false;

	//	cv::rectangle(frame, cv::Point(17 + m_iTrackingOffset, 237), cv::Point(22 - 1 + m_iTrackingOffset, 237 + 8 - 1), cv::Scalar(0, 0, 200), 1, 1);
	//}

	// Check Note Hole
	for (int n = m_iLowestNoteNo; n <= m_iHighestNoteNo; ++n){

		dAvg = 0;

		for (int y = 240; y < m_iNoteHoleHeigth + 240; y++){
			for (int x = m_iNote_x[n] + m_iTrackingOffset; x < m_iNoteHoleHeigth + m_iNote_x[n] + m_iTrackingOffset; ++x){

				//  Blue 
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
	cv::line(frame, cv::Point(5, 235), cv::Point(5, 245), cv::Scalar(200, 0, 200), 1, 4);
	cv::line(frame, cv::Point(635, 235), cv::Point(635, 245), cv::Scalar(200, 0, 200), 1, 4);
	cv::line(frame, cv::Point(0, 255), cv::Point(639, 255), cv::Scalar(100, 100, 0), 1, 4);
	cv::line(frame, cv::Point(0, 212), cv::Point(639, 212), cv::Scalar(100, 100, 0), 1, 4);

	mycv::cvtMat2HDC()(g_hdcImage, frame);

	return 0;
}



// Load 88-note setting 
int Player::LoadPlayerSettings()
{

	char buf[256];
	std::ifstream ifs;

	ifs.open("88-Note.txt");
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
	for (int i = m_iLowestNoteNo; i <= m_iHighestNoteNo; ++i){
		ifs.getline(buf, sizeof(buf));
		m_iNote_x[i] = atoi(buf);
	}


	ifs.close();

	return 0;
}

void Player::SendMidiMsg(const HMIDIOUT &hm)
{

	// Send Bass Stack Note Msg
	for (int iKey = 0; iKey < m_iStackDevide; ++iKey){
		if (m_cNoteOn[iKey] == onTriger){
			NoteOnMsg(iKey + 21, m_iBassStackVelo, hm);
			m_cNoteOn[iKey] = on;
		}
		else if (m_cNoteOn[iKey] == offTriger){
			NoteOffMsg(iKey + 21, hm);
			m_cNoteOn[iKey] = off;
		}
	}

	// Send Treble Note Msg
	for (int iKey = m_iStackDevide; iKey < KeyNum; ++iKey){
		if (m_cNoteOn[iKey] == onTriger){
			NoteOnMsg(iKey + 21, m_iTrebleStackVelo, hm);
			m_cNoteOn[iKey] = on;
		}
		else if (m_cNoteOn[iKey] == offTriger){
			NoteOffMsg(iKey + 21, hm);
			m_cNoteOn[iKey] = off;
		}
	}

	// Send Pedal Msg
	if (m_cSusteinPedalOn == onTriger){
		SusteinP(true, hm);
		m_cSusteinPedalOn = on;
	}
	else if (m_cSusteinPedalOn == offTriger){
		SusteinP(false, hm);
		m_cSusteinPedalOn = off;
	}

	if (m_cSoftPedalOn == onTriger){
		SoftP(true, hm);
		m_cSoftPedalOn = on;
	}
	else if (m_cSoftPedalOn == offTriger){
		SoftP(false, hm);
		m_cSoftPedalOn = off;
	}
}