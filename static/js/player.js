// Basic player integration + listening history logging
// Assumes rows with data-mp3-path and data-title are clickable or selected elsewhere.

// Prevent duplicate execution
if (window.playerJsInitialized) {
    // Already initialized, skipping silently
} else {
    window.playerJsInitialized = true;

(function() {
    'use strict';

if (!window.audioEl) {
    window.audioEl = document.getElementById('audio-player');
}
const audioEl = window.audioEl;
// Use window.currentSongId so app.js can set it
window.currentSongId = window.currentSongId || null;
window.thresholdLogged = window.thresholdLogged || false;
const lastPlayLog = {}; // songId -> timestamp ms (throttle across plays)
// Track logged play sessions so navigation or re-render won't cause duplicate logs
const loggedPlaySessions = new Set(); // playSessionId strings
const logInProgress = {}; // playSessionId -> boolean while fetch in-flight
window.currentPlaySession = window.currentPlaySession || null;

// Persistence helpers so play-session dedupe survives SPA navigation
function _loadLoggedPlaySessionsFromStorage(){
	try{
		const arr = JSON.parse(sessionStorage.getItem('loggedPlaySessions') || '[]');
		if(Array.isArray(arr)) arr.forEach(a=>{ if(a) loggedPlaySessions.add(a); });
	}catch(e){ /* ignore */ }
}
function _saveLoggedPlaySessionsToStorage(){
	try{ sessionStorage.setItem('loggedPlaySessions', JSON.stringify(Array.from(loggedPlaySessions))); }catch(e){}
}
function _setCurrentPlaySession(ps){
	try{ if(ps) sessionStorage.setItem('currentPlaySession', ps); else sessionStorage.removeItem('currentPlaySession'); }catch(e){}
	try{ window.currentPlaySession = ps || null; }catch(e){}
}

// Initialize from sessionStorage on load
try{ _loadLoggedPlaySessionsFromStorage(); _setCurrentPlaySession(sessionStorage.getItem('currentPlaySession') || null); }catch(e){}


function getCookieToken(){
	const token = document.cookie.split('; ').find(r=>r.startsWith('access_token='));
	return token ? token.split('=')[1] : null;
}
function authHeaders(){
	const h={'Content-Type':'application/json'};
	const tokenLocal = localStorage.getItem('access_token');
	const tokenCookie = getCookieToken();
	const token = tokenLocal || tokenCookie;
	if(token) h['Authorization'] = 'Bearer ' + token;
	return h;
}

function logListen(songId, playSessionId){
	if(!songId) return;
	const ps = playSessionId || window.currentPlaySession || String(songId);
	// Prevent duplicate for same playback session (optimistic set)
	if(loggedPlaySessions.has(ps) || logInProgress[ps]){
		console.debug('[DEBUG] Skipping logListen: already logged or in-progress', {songId, playSession: ps, alreadyLogged: loggedPlaySessions.has(ps), inProgress: !!logInProgress[ps]});
		return;
	}

	// Mark as in-progress and reserved so concurrent events don't trigger duplicates
	logInProgress[ps] = true;
	loggedPlaySessions.add(ps);
	_saveLoggedPlaySessionsToStorage();
	const now = Date.now();
	// Throttle global spam (still allow first legitimate log after threshold)
	if(lastPlayLog[songId] && (now - lastPlayLog[songId] < 8000)) {
		console.debug('[DEBUG] Skipping logListen: throttled by lastPlayLog', {songId, last: lastPlayLog[songId], now});
		return;
	}
	lastPlayLog[songId] = now;
	fetch('/api/history/log', {
		method:'POST',
		headers: authHeaders(),
		credentials:'include',
		body: JSON.stringify({song_id: songId})
	})
	.then(r=>{
		console.debug('[DEBUG] /api/history/log response status', r.status, 'ok=', r.ok);
		return r.json().then(j=>({ok:r.ok,data:j})).catch(err=>{
			console.debug('[DEBUG] Failed to parse JSON response from /api/history/log', err);
			return { ok: r.ok, data: null, parseError: String(err), status: r.status };
		});
	})
	.then(obj=>{ 
		if(!obj.ok){
			console.debug('Listen log failed', obj.data);
			// if failed, allow retry in future by removing session reservation
			loggedPlaySessions.delete(ps);
			_saveLoggedPlaySessionsToStorage();
		} else {
			console.debug('Logged play for song', songId, obj.data);
			// If server returned authoritative total listens, use it to set UI exactly.
			const total = (obj.data && (typeof obj.data.total_listens === 'number' || !isNaN(Number(obj.data.total_listens)))) ? Number(obj.data.total_listens) : null;
			if(total !== null){
				try{ setListenCount(songId, total); } catch(e){ console.debug('setListenCount failed', e); }
			} else {
				try{ incrementListenCount(songId, 1); } catch(e){ console.debug('incrementListenCount failed', e); }
			}
		}
	})
	.catch(err=>{
		console.debug('Listen log error', err);
		// network error: clear reservation so a future attempt can retry
		loggedPlaySessions.delete(ps);
		_saveLoggedPlaySessionsToStorage();
	})
	.finally(()=>{ try{ delete logInProgress[ps]; }catch(e){} });
}

// Update DOM listen counts and any in-memory caches when a listen is logged.
function setListenCount(songId, total){
	try{
		const sid = String(songId);
		// Find all listen-count spans for this song and set to total
		document.querySelectorAll(`tr.song-row[data-song-id="${sid}"] .listen-count span`).forEach(el=>{
			el.textContent = Number(total || 0);
		});
		// Also update any generic .listen-count[data-song-id] usages
		document.querySelectorAll(`.listen-count[data-song-id="${sid}"]`).forEach(el=>{
			el.textContent = Number(total || 0);
		});
		// Update playlist cache if present
		if(window._playlistCache && window._playlistCache.data && Array.isArray(window._playlistCache.data.songs)){
			const song = window._playlistCache.data.songs.find(s=>String(s.id) === sid);
			if(song){ song.listen_count = Number(total || 0); }
		}
		// Update other caches (app-level) if present
		if(window._songCache && window._songCache[sid]){
			window._songCache[sid].listen_count = Number(total || 0);
		}
	}catch(e){ console.debug('setListenCount error', e); }
}

function incrementListenCount(songId, delta=1){
	try{
		const sid = String(songId);
		// Try to increment existing displayed counts; fallback to set 1
		let updated = false;
		document.querySelectorAll(`tr.song-row[data-song-id="${sid}"] .listen-count span`).forEach(el=>{
			const cur = parseInt(el.textContent || '0',10) || 0;
			el.textContent = cur + delta;
			updated = true;
		});
		document.querySelectorAll(`.listen-count[data-song-id="${sid}"]`).forEach(el=>{
			const cur = parseInt(el.textContent || '0',10) || 0;
			el.textContent = cur + delta;
			updated = true;
		});
		if(!updated){
			// nothing to increment; try setting to delta
			setListenCount(sid, delta);
		}
		// Update caches conservatively (increment)
		if(window._playlistCache && window._playlistCache.data && Array.isArray(window._playlistCache.data.songs)){
			const song = window._playlistCache.data.songs.find(s=>String(s.id) === sid);
			if(song){ song.listen_count = (Number(song.listen_count) || 0) + delta; }
		}
		if(window._songCache && window._songCache[sid]){
			window._songCache[sid].listen_count = (Number(window._songCache[sid].listen_count) || 0) + delta;
		}
	}catch(e){ console.debug('incrementListenCount error', e); }
}


// Check threshold (10s) for logging
function handleTimeUpdate(){
	// Only log when there's an active song and audio is actually playing
	try{
		if(!window.currentSongId){ console.debug('[DEBUG] handleTimeUpdate skip: no currentSongId'); return; }
		if(window.thresholdLogged){ console.debug('[DEBUG] handleTimeUpdate skip: threshold already logged for session', window.currentPlaySession); return; }
		if(audioEl.paused || audioEl.readyState < 2){ console.debug('[DEBUG] handleTimeUpdate skip: audio paused or not ready', {paused: audioEl.paused, readyState: audioEl.readyState}); return; }
		// If duration < 11s, we'll log at ended instead for very short tracks
		if(audioEl.duration && audioEl.duration < 11) return;
		if(audioEl.currentTime >= 10){
			console.log('[DEBUG] Threshold reached, logging song:', window.currentSongId, 'session:', window.currentPlaySession, 'currentTime:', audioEl.currentTime);
			logListen(Number(window.currentSongId), window.currentPlaySession);
			window.thresholdLogged = true;
		}
	}catch(e){ console.debug('handleTimeUpdate error', e); }
}
audioEl?.addEventListener('timeupdate', handleTimeUpdate);

// Example function to play a song when row clicked
function bindSongRows(){
	document.querySelectorAll('.song-row').forEach(row => {
		row.addEventListener('click', function(e){
			// ignore clicks on remove buttons
			if(e.target.classList.contains('remove-song-btn')) return;
			const mp3 = row.getAttribute('data-mp3-path');
			const sid = row.getAttribute('data-song-id');
			if(mp3){
				audioEl.src = mp3;
				// For a manual play start we create a fresh play session id.
				try{
					const ps = sid ? (String(sid) + ':' + String(Date.now())) : null;
					_setCurrentPlaySession(ps);
				} catch(e){ _setCurrentPlaySession(null); }
				// Reset threshold flag only when starting a new play session
				try{ window.thresholdLogged = false; }catch(e){}
				window.currentSongId = sid || null;
				audioEl.play().catch(()=>{});
			}
		});
	});
}

document.addEventListener('DOMContentLoaded', function(){
	bindSongRows();
	// Re-bind after dynamic playlist reloads
	const observer = new MutationObserver(()=>bindSongRows());
	const container = document.getElementById('playlist-songs');
	if(container) observer.observe(container, {childList:true, subtree:true});

	// Also observe BXH ranking list when it exists so clicks on ranking rows play audio
	const bxhContainer = document.getElementById('bxh-song-list');
	if(bxhContainer){
		// Bind initially in case server rendered rows exist
		bindSongRows();
		const bxhObserver = new MutationObserver(()=>bindSongRows());
		bxhObserver.observe(bxhContainer, {childList:true, subtree:true});
	}
});

// Log listen when audio ends and restarts next (placeholder for future next-track logic)
audioEl?.addEventListener('ended', ()=>{
	// For very short tracks (<11s) that never reached 10s threshold
	if(window.currentSongId && !window.thresholdLogged && audioEl.duration && audioEl.duration < 11){
		logListen(Number(window.currentSongId));
		window.thresholdLogged = true;
	}
	// Future: advance queue logic could go here
});

})(); // End IIFE
} // End duplicate check
