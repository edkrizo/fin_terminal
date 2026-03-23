window.mercuryAudioContext = null;
window.mercuryMicStream = null;
window.mercuryWebSocket = null;
window.mercuryNextPlayTime = 0;
window.mercuryLastSpeechTime = Date.now();
window.mercuryIdlePingInterval = null;

/**
 * Initializes the WebRTC and WebSocket engine for Gemini Multimodal Live.
 * 
 * 1. Prompts the user for OS microphone access.
 * 2. Establishes a raw WebSocket proxy tunnel via the FastAPI /ws/live endpoint.
 * 3. Injects the active state of the user's dashboard straight into Gemini's memory.
 * 4. Resamples the local Float32 microphone buffer to strict 16kHz PCM binaries needed by Vertex.
 * 5. Handles inbound WebSocket JSON objects instructing Reflex to 'trigger_massive_query' 
 *    or 'switch_view' to manipulate the frontend purely via Agentic commands.
 * 
 * @param {string} persona - Explicit persona profile (e.g. Fundamental Analyst)
 * @param {string} dashboardContext - Escaped JSON string of the active UI tables/news
 */
window.startMercuryLive = async function(persona, dashboardContext) {
    console.log(`🎙️ Requesting microphone access for Persona: ${persona}...`);
    
    try {
        // 1. Get Microphone Permissions
        window.mercuryMicStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // 2. Set up Audio Context (Gemini strictly requires 16kHz)
        window.mercuryAudioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        window.mercuryNextPlayTime = window.mercuryAudioContext.currentTime;
        
        // 3. Open WebSocket
        // 🚀 THE FIX 2: Pass the active persona as a query parameter to FastAPI
        const safePersona = encodeURIComponent(persona || "Fundamental Analyst");
        window.mercuryWebSocket = new WebSocket(`ws://127.0.0.1:8080/ws/live?persona=${safePersona}`);
        window.mercuryWebSocket.binaryType = 'arraybuffer'; 

        // 🚀 THE FIX 3: Inject the Dashboard State immediately upon connection!
        window.mercuryWebSocket.onopen = () => {
            console.log("✅ Live Voice channel established. Injecting dashboard context...");
            if (dashboardContext) {
                // Send the JSON string to the server so it can be pushed into Gemini's memory
                window.mercuryWebSocket.send(dashboardContext);
            }
            
            // ⏸️ Pause the podcast explicitly if it was playing since they are interrupting it
            const audioEls = document.querySelectorAll('audio');
            if (audioEls.length > 0) {
                console.log("⏸️ Pausing podcast audio for interruption...");
                try { audioEls[0].pause(); } catch(e) {}
            }
            
            // --- IDLE STATUS PINGER ---
            if (window.mercuryIdlePingInterval) clearInterval(window.mercuryIdlePingInterval);
            window.mercuryLastSpeechTime = Date.now();
            window.mercuryIdlePingInterval = setInterval(() => {
                if (!window.mercuryWebSocket || window.mercuryWebSocket.readyState !== WebSocket.OPEN) return;
                
                // Do not ping if the AI is actively speaking
                if (window.mercuryNextPlayTime > window.mercuryAudioContext.currentTime) return;
                
                const now = Date.now();
                const silentSeconds = (now - window.mercuryLastSpeechTime) / 1000;
                
                // If the user has been silent for 10 seconds, send an async status ping
                if (silentSeconds > 10) {
                    const pingPayload = JSON.stringify({
                         "action": "idle_ping"
                    });
                    window.mercuryWebSocket.send(pingPayload);
                    window.mercuryLastSpeechTime = now; // reset timer to prevent spamming
                }
            }, 5000);
        };

        // 4. Capture and Resample Mic Audio
        const source = window.mercuryAudioContext.createMediaStreamSource(window.mercuryMicStream);
        const processor = window.mercuryAudioContext.createScriptProcessor(1024, 1, 1);
        
        source.connect(processor);
        processor.connect(window.mercuryAudioContext.destination);
        
        processor.onaudioprocess = (e) => {
            if (window.mercuryWebSocket && window.mercuryWebSocket.readyState === WebSocket.OPEN) {
                
                // --- MICROPHONE AUTO-ECHO MUTE: Skip sending frames if Bot is actively speaking ---
                const isBotSpeaking = window.mercuryNextPlayTime > window.mercuryAudioContext.currentTime + 0.1; 
                if (isBotSpeaking) {
                    return;
                }

                const inputData = e.inputBuffer.getChannelData(0);
                
                // Track Voice Activity locally to reset the idle timer
                let isSpeaking = false;
                
                // CRITICAL: Convert Float32 to PCM 16-bit
                const pcm16 = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const sample = inputData[i];
                    if (Math.abs(sample) > 0.05) isSpeaking = true;
                    pcm16[i] = Math.max(-1, Math.min(1, sample)) * 32767;
                }
                
                if (isSpeaking) {
                    window.mercuryLastSpeechTime = Date.now();
                }
                
                window.mercuryWebSocket.send(pcm16.buffer);
            }
        };

        // 5. Receive Voice or Commands from Server
        window.mercuryWebSocket.onmessage = async (event) => {
            
            // CHECK 1: Did the server send a TEXT command to close the mic?
            if (typeof event.data === "string") {
                if (event.data === "CLOSE_MIC") {
                    console.log("🛑 Gemini requested closing session. Auto-closing microphone...");
                    
                    // 🚀 THE FIX: Use innerText for robust button selection in React/Reflex
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const stopBtn = buttons.find(b => b.innerText.includes("Stop Interrupt"));
                    
                    if (stopBtn) {
                        console.log("👉 Simulating click on Stop Interrupt button...");
                        stopBtn.click();
                        
                        // ▶️ Auto-resume the podcast natively!
                        setTimeout(() => {
                            const audioEls = document.querySelectorAll('audio');
                            if (audioEls.length > 0) {
                                console.log("▶️ Resuming podcast audio automatically...");
                                try { audioEls[0].play(); } catch(e) {}
                            }
                        }, 500); // 500ms delay to allow Reflex state to finalize
                    } else {
                        console.log("⚠️ Could not find 'Stop Interrupt' button to auto-close mic.");
                    }
                    return;
                } else if (event.data === "INTERRUPT") {
                    console.log("⚠️ Interrupted! Clearing audio queue...");
                    window.mercuryNextPlayTime = window.mercuryAudioContext.currentTime;
                    return;
                }
                
                // --- AGENTIC VIEW SWITCH OVERRIDE ---
                if (event.data.startsWith("{")) {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.action === "switch_view") {
                            console.log("🔄 Agent requested view switch:", data);
                            const inputTicker = document.getElementById("live_ticker_input");
                            const inputTab = document.getElementById("live_tab_input");
                            const triggerBtn = document.getElementById("live_trigger_btn");
                            
                            if (inputTicker && inputTab && triggerBtn) {
                                // Standard React 16+ input bridge prototype override
                                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                
                                nativeInputValueSetter.call(inputTicker, data.security_ticker || "");
                                nativeInputValueSetter.call(inputTab, data.tab_name || "Company/Security");
                                
                                inputTicker.dispatchEvent(new Event('input', { bubbles: true }));
                                inputTab.dispatchEvent(new Event('input', { bubbles: true }));
                                
                                setTimeout(() => { triggerBtn.click(); }, 100);
                            }
                            return;
                         } else if (data.action === "trigger_massive_query") {
                             console.log("🚀 Agent requested massive async query:", data);
                             const inputQuery = document.getElementById("live_massive_query_input");
                             const triggerBtn = document.getElementById("live_massive_trigger_btn");
                             if (inputQuery && triggerBtn) {
                                  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                  // Clear input then set the massive query
                                  nativeInputValueSetter.call(inputQuery, data.query || "");
                                  inputQuery.dispatchEvent(new Event('input', { bubbles: true }));
                                  
                                  setTimeout(() => { triggerBtn.click(); }, 100);
                             }
                             return;
                         }
                    } catch (e) {
                         console.error("Failed to parse socket command:", e);
                    }
                }
            }

            // CHECK 2: Otherwise, it is binary audio bytes. Play them!
            if (event.data instanceof ArrayBuffer) {
                const pcm16 = new Int16Array(event.data);
                const float32 = new Float32Array(pcm16.length);
                for (let i = 0; i < pcm16.length; i++) {
                    float32[i] = pcm16[i] / 32768.0; 
                }
                
                const audioBuffer = window.mercuryAudioContext.createBuffer(1, float32.length, 24000);
                audioBuffer.getChannelData(0).set(float32);
                
                const playSource = window.mercuryAudioContext.createBufferSource();
                playSource.buffer = audioBuffer;
                playSource.connect(window.mercuryAudioContext.destination);
                
                if (window.mercuryNextPlayTime < window.mercuryAudioContext.currentTime) {
                    window.mercuryNextPlayTime = window.mercuryAudioContext.currentTime;
                }
                
                playSource.start(window.mercuryNextPlayTime);
                window.mercuryNextPlayTime = window.mercuryNextPlayTime + audioBuffer.duration;
            }
        };

    } catch (error) {
        console.error("❌ Failed to start Live Voice:", error);
    }
};

window.stopMercuryLive = function() {
    console.log("🔇 Stopping Live Voice...");
    if (window.mercuryWebSocket) {
        // Send a final close signal to the server so it cleanly kills the session
        if (window.mercuryWebSocket.readyState === WebSocket.OPEN) {
            window.mercuryWebSocket.send("CLOSE_MIC");
        }
        window.mercuryWebSocket.close();
        window.mercuryWebSocket = null;
    }
    if (window.mercuryMicStream) {
        window.mercuryMicStream.getTracks().forEach(track => track.stop());
        window.mercuryMicStream = null;
    }
    if (window.mercuryAudioContext) {
        window.mercuryAudioContext.close();
        window.mercuryAudioContext = null;
    }
};