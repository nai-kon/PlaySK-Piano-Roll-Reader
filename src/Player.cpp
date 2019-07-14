
#include "stdafx.h"
#include "Player.h"


Player::Player()
{
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
}

Player::~Player()
{

}


// Load 88-note setting 
int Player::LoadPlayerSettings()
{
	std::ifstream ifs("config\\88_tracker.json");
	std::string err, strjson((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
	json11::Json json = json11::Json::parse(strjson, err);

	auto obj = json["expression"];
	m_iBassStackVelo = m_iTrebleStackVelo = obj["velocity"].int_value();

	obj = json["tracker_holes"];
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
	cv::line(frame, cv::Point(5, 235), cv::Point(5, 245), cv::Scalar(200, 0, 200), 1, 4);
	cv::line(frame, cv::Point(635, 235), cv::Point(635, 245), cv::Scalar(200, 0, 200), 1, 4);
	cv::line(frame, cv::Point(0, 255), cv::Point(639, 255), cv::Scalar(100, 100, 0), 1, 4);
	cv::line(frame, cv::Point(0, 212), cv::Point(639, 212), cv::Scalar(100, 100, 0), 1, 4);

	return 0;
}


void Player::EmulateVelocity(cv::Mat &frame)
{
	// 88-note emulation sets stable, so no changes
	// m_iBassStackVelo = m_iTrebleStackVelo = ;
}


void Player::EmulatePedal(cv::Mat &frame)
{
	// Check Sustein Pedal Hole
	double dAvg = GetAvgHoleBrightness(frame, m_rcSustainPedal);
	if (dAvg < m_rcSustainPedal.th_on && m_SusteinPedalOn == off && m_bEmulateOn) {
		m_SusteinPedalOn = onTriger;
	}
	else if (dAvg > m_rcSustainPedal.th_off && m_SusteinPedalOn == on) {
		m_SusteinPedalOn = offTriger;
	}
	bool hole_on = (m_SusteinPedalOn > 0 && m_bEmulateOn);
	DrawHole(frame, m_rcSustainPedal, hole_on);


	// Check Soft Pedal Hole
	dAvg = GetAvgHoleBrightness(frame, m_rcSoftPedal);
	if (dAvg < m_rcSustainPedal.th_on && m_SoftPedalOn == off && m_bEmulateOn) {
		m_SoftPedalOn = onTriger;
	}
	else if (dAvg > m_rcSustainPedal.th_off && m_SoftPedalOn == on) {
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

		double dAvg = GetAvgHoleBrightness(frame, m_rcNote[key]);
		if (m_NoteOn[key] == off && dAvg < m_rcNote[key].th_on && m_bEmulateOn) {
			if (m_iNoteOnCnt[key] >= m_iNoteOnFrames) {
				m_iNoteOnCnt[key] = 0;
				m_NoteOn[key] = onTriger;
			}
			else {
				m_iNoteOnCnt[key]++;
			}
		}
		else if (m_NoteOn[key] == on && dAvg > m_rcNote[key].th_off) {
			m_NoteOn[key] = offTriger;
		}
		bool hole_on = (m_NoteOn[key] > 0 && m_bEmulateOn);
		DrawHole(frame, m_rcNote[key], hole_on);
	}
}


double Player::GetAvgHoleBrightness(cv::Mat &frame, const TRACKER_HOLE &hole)
{
	double dSumBrightness = 0;
	int hole_y_bottom = hole.y + hole.h;
	int hole_x_left = hole.x + m_iTrackingOffset;
	int hole_x_right = hole.x + hole.w + m_iTrackingOffset;
	for (int y = hole.y; y < hole_y_bottom; y++) {
		int yoffset = y * VIDEO_WIDTH * 3;
		for (int x = hole_x_left; x < hole_x_right; x++) {
			// only read blue channel instead of b/w image
			dSumBrightness += frame.data[yoffset + 3 * x];
		}
	}

	// return average brightness
	return dSumBrightness / (hole.w * hole.h);
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
		json["th_on"].int_value(),
		json["th_off"].int_value()
	};
}

void Player::SetHoleRectListFromJsonObj(const json11::Json json, TRACKER_HOLE *prcSetHole, UINT rect_cnt) {

	if (prcSetHole == NULL) {
		return;
	}

	int note_y = json["y"].int_value();
	int note_w = json["w"].int_value();
	int note_h = json["h"].int_value();
	int th_on = json["th_on"].int_value();
	int th_off = json["th_off"].int_value();
	std::vector<json11::Json> xpos = json["x"].array_items();
	for (UINT i = 0; i < rect_cnt && i < xpos.size(); i++) {
		prcSetHole[i] = {
			xpos[i].int_value(),
			note_y,
			note_w,
			note_h,
			th_on,
			th_off
		};
	}
}
