
#include "stdafx.h"
#include "Player.h"


Player::Player()
{
	m_iBassStackVelo = m_iTrebleStackVelo = 0;
	m_SusteinPedalOn = m_SoftPedalOn = off;
	for (int i = 0; i < KeyNum; ++i) {
		m_NoteOn[i] = off;
		m_iNoteOnCnt[i] = 0;
	}

	m_iNoteOnFrames = 0;
	m_iTrackingOffset = 0;
	m_dFrameRate = 0;
	m_bEmulateOn = false;

	m_uiStackSplitPoint = 43; 
	m_bIsDarkHole = true;
	m_iHoleOnth = 0;
}

Player::~Player()
{

}


// Load 88-note setting 
int Player::LoadPlayerSettings(LPCTSTR config_path)
{
	std::ifstream ifs(config_path);
	std::string err, strjson((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
	json11::Json json = json11::Json::parse(strjson, err);

	auto obj = json["expression"];
	m_iBassStackVelo = m_iTrebleStackVelo = obj["velocity"].int_value();
	obj = json["tracker_holes"];
	m_bIsDarkHole = obj["is_dark_hole"].bool_value();
	m_iHoleOnth = obj["on_brightness"].bool_value();
	SetHoleRectFromJsonObj(obj["sustain"], m_rcSustainPedal);
	SetHoleRectFromJsonObj(obj["soft"], m_rcSoftPedal);
	SetHoleRectListFromJsonObj(obj["note"], m_rcNote, KeyNum);
	
	if (err.size() > 0) return -1;
	return 0;
}


// emulate vitrual tracker bar
int Player::Emulate(cv::Mat &frame, const HMIDIOUT &hm)
{
	// Send buffered midi msg
	SendMidiMsg(hm);
	
	// Check tracker holes, draw and emulate it 
	EmulateVelocity(frame);
	EmulatePedal(frame);
	EmulateNote(frame);

	// Draw tracker-bar frame
	cv::line(frame, cv::Point(4, 235), cv::Point(4, 245), cv::Scalar(200, 0, 200), 1, 4);
	cv::line(frame, cv::Point(635, 235), cv::Point(635, 245), cv::Scalar(200, 0, 200), 1, 4);
	cv::line(frame, cv::Point(0, 255), cv::Point(639, 255), cv::Scalar(100, 100, 0), 1, 4);
	cv::line(frame, cv::Point(0, 212), cv::Point(639, 212), cv::Scalar(100, 100, 0), 1, 4);

	return 0;
}


// emulate vitrual tracker bar
int Player::GetTrackerOffset(const cv::Mat &frame)
{

	// right end
	int right_offset = 0;
	for (int y = 235; y < 245; y++) { // check average offset
		int yidx = y * VIDEO_WIDTH * 3; // half height
		for (int x = 4; x >= 0; x--) {
			int idx = yidx + 3 * x;
			int b = frame.data[idx + 0];
			int g = frame.data[idx + 1];
			int r = frame.data[idx + 2];
			if (m_bIsDarkHole) {
				if (b > m_iHoleOnth && g > m_iHoleOnth && r > m_iHoleOnth) right_offset++;
			}
			else {
				if (b < m_iHoleOnth && g < m_iHoleOnth && r < m_iHoleOnth) right_offset++;
			}
		}
	}
	right_offset /= 10;

	// left end
	int left_offset = 0;
	for (int y = 235; y < 245; y++) { // check average offset
		int yidx = y * VIDEO_WIDTH * 3; // half height
		for (int x = 635; x < VIDEO_WIDTH; x++) {
			int idx = yidx + 3 * x;
			int b = frame.data[idx + 0];
			int g = frame.data[idx + 1];
			int r = frame.data[idx + 2];
			if (m_bIsDarkHole) {
				if (b > m_iHoleOnth && g > m_iHoleOnth && r > m_iHoleOnth) left_offset++;
			}
			else {
				if (b < m_iHoleOnth && g < m_iHoleOnth && r < m_iHoleOnth) left_offset++;
			}
		}
	}
	left_offset /= 10;

	return left_offset - right_offset;
}


void Player::EmulateVelocity(cv::Mat &frame)
{
	// 88-note emulation sets stable, so no changes
	// m_iBassStackVelo = m_iTrebleStackVelo = ;
}


void Player::EmulatePedal(cv::Mat &frame)
{
	// Check Sustein Pedal Hole
	double dAvg = GetHoleApatureRatio(frame, m_rcSustainPedal);
	if (m_SusteinPedalOn == off && isHoleOn(dAvg, m_rcSustainPedal.on_apature) && m_bEmulateOn) {
		m_SusteinPedalOn = onTriger;
	}
	else if (m_SusteinPedalOn == on && isHoleOff(dAvg, m_rcSustainPedal.off_apature)) {
		m_SusteinPedalOn = offTriger;
	}
	bool hole_on = (m_SusteinPedalOn > 0 && m_bEmulateOn);
	DrawHole(frame, m_rcSustainPedal, hole_on);


	// Check Soft Pedal Hole
	dAvg = GetHoleApatureRatio(frame, m_rcSoftPedal);
	if (m_SoftPedalOn == off && isHoleOn(dAvg, m_rcSoftPedal.on_apature) && m_bEmulateOn) {
		m_SoftPedalOn = onTriger;
	}
	else if (m_SoftPedalOn == on && isHoleOff(dAvg, m_rcSoftPedal.off_apature)) {
		m_SoftPedalOn = offTriger;
	}
	hole_on = (m_SoftPedalOn > 0 && m_bEmulateOn);
	DrawHole(frame, m_rcSoftPedal, hole_on);
}


void Player::EmulateNote(cv::Mat &frame)
{
	// Check note holes
	for (int key = 0; key < KeyNum; key++) {

		// skip for dummy position
		if (m_rcNote[key].x == 0) continue;

		double dAvg = GetHoleApatureRatio(frame, m_rcNote[key]);
		if (m_NoteOn[key] == off && isHoleOn(dAvg, m_rcNote[key].on_apature) && m_bEmulateOn) {
			if (m_iNoteOnCnt[key] >= m_iNoteOnFrames) {
				m_iNoteOnCnt[key] = 0;
				m_NoteOn[key] = onTriger;
			}
			else {
				m_iNoteOnCnt[key]++;
			}
		}
		else if (m_NoteOn[key] == on && isHoleOff(dAvg, m_rcNote[key].off_apature)) {
			m_NoteOn[key] = offTriger;
		}
		bool hole_on = (m_NoteOn[key] > 0 && m_bEmulateOn);
		DrawHole(frame, m_rcNote[key], hole_on);
	}
}



double Player::GetHoleApatureRatio(cv::Mat &frame, const TRACKER_HOLE &hole)
{
	double dSumBrightness = 0;
	int hole_y_bottom = hole.y + hole.h;
	int hole_x_left = hole.x + m_iTrackingOffset;
	int hole_x_right = hole_x_left + hole.w;
	int hole_on_pixs = 0;
	for (int y = hole.y; y < hole_y_bottom; y++) {
		int yoffset = y * VIDEO_WIDTH * 3;
		for (int x = hole_x_left; x < hole_x_right; x++) {
			int idx = yoffset + 3 * x;
			int b = frame.data[idx + 0];
			int g = frame.data[idx + 1];
			int r = frame.data[idx + 2];
			if (m_bIsDarkHole) {
				if (b < m_iHoleOnth && g < m_iHoleOnth && r < m_iHoleOnth) hole_on_pixs++;
			}
			else {
				if (b > m_iHoleOnth && g > m_iHoleOnth && r > m_iHoleOnth) hole_on_pixs++;
			}
		}
	}

	// return on hole apature ratio
	return (double)hole_on_pixs / (hole.w * hole.h);
}


bool Player::isHoleOn(double dApatureRatio, double dOnRatio) {
	//if (dApatureRatio > 0) {

	//	TCHAR strBuf[20];
	//	wsprintf(strBuf, _T("ratio : %d \n"), (int)(100 * dApatureRatio));
	//	OutputDebugString(strBuf);
	//}

	return dApatureRatio > dOnRatio;
}


bool Player::isHoleOff(double dApatureRatio, double dOffRatio) {
	return dApatureRatio < dOffRatio;
}


void Player::DrawHole(cv::Mat &frame, const TRACKER_HOLE &hole, bool hole_on)
{
	// hole on : red colored, hole off : blue colored
	auto hole_color = hole_on ? cv::Scalar(0, 0, 200) : cv::Scalar(200, 0, 0);

	cv::Rect drawHole(hole.x, hole.y, hole.w, hole.h);
	drawHole.x += m_iTrackingOffset;

	cv::rectangle(frame, drawHole, hole_color);
}


int Player::GetMinVelocity() 
{
	// min velocity is stable at 88note mode
	return m_iBassStackVelo;
}


int Player::GetMaxVelocity() 
{
	// max velocity is stable at 88note mode
	return m_iBassStackVelo;
}


int Player::NoteAllOff(const HMIDIOUT &hm)
{
	m_SoftPedalOn = offTriger;
	m_SusteinPedalOn = offTriger;
	for (UINT key = 0; key < KeyNum; key++) {
		m_NoteOn[key] = offTriger;
		m_iNoteOnCnt[key] = 0;
	}

	SendMidiMsg(hm);

	return 0;
}


void Player::SendMidiMsg(const HMIDIOUT &hm)
{
	// Send Bass Stack Note Msg
	for (UINT key = 0; key < m_uiStackSplitPoint; key++){
		if (m_NoteOn[key] == onTriger){
			NoteOnMsg(key + 21, m_iBassStackVelo, hm);
			m_NoteOn[key] = on;
		}
		else if (m_NoteOn[key] == offTriger){
			NoteOffMsg(key + 21, hm);
			m_NoteOn[key] = off;
		}
	}

	// Send Treble Note Msg
	for (UINT key = m_uiStackSplitPoint; key < KeyNum; key++){
		if (m_NoteOn[key] == onTriger){
			NoteOnMsg(key + 21, m_iTrebleStackVelo, hm);
			m_NoteOn[key] = on;
		}
		else if (m_NoteOn[key] == offTriger){
			NoteOffMsg(key + 21, hm);
			m_NoteOn[key] = off;
		}
	}

	// Send Pedal Msg
	if (m_SusteinPedalOn == onTriger){
		SusteinP(true, hm);
		m_SusteinPedalOn = on;
	}
	else if (m_SusteinPedalOn == offTriger){
		SusteinP(false, hm);
		m_SusteinPedalOn = off;
	}

	if (m_SoftPedalOn == onTriger){
		SoftP(true, hm);
		m_SoftPedalOn = on;
	}
	else if (m_SoftPedalOn == offTriger){
		SoftP(false, hm);
		m_SoftPedalOn = off;
	}
}


void Player::SetHoleRectFromJsonObj(const json11::Json json, TRACKER_HOLE &rcSetHole) {
	rcSetHole = {
		json["x"].int_value(),
		json["y"].int_value(),
		json["w"].int_value(),
		json["h"].int_value(),
		json["on_apature"].number_value(),
		json["off_apature"].number_value(),
	};
}

void Player::SetHoleRectListFromJsonObj(const json11::Json json, TRACKER_HOLE *prcSetHole, UINT rect_cnt) {

	if (prcSetHole == NULL) {
		return;
	}

	int note_y = json["y"].int_value();
	int note_w = json["w"].int_value();
	int note_h = json["h"].int_value();
	double on_apature = json["on_apature"].number_value();
	double off_apature = json["off_apature"].number_value();
	std::vector<json11::Json> xpos = json["x"].array_items();
	for (UINT i = 0; i < rect_cnt && i < xpos.size(); i++) {
		prcSetHole[i] = {
			xpos[i].int_value(),
			note_y,
			note_w,
			note_h,
			on_apature,
			off_apature,
		};
	}
}

