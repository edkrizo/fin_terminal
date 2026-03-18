window.mercuryAudioContext = null;
window.mercuryMicStream = null;
window.mercuryWebSocket = null;
window.mercuryNextPlayTime = 0;

// 🚀 THE FIX 1: Accept the persona and dashboardContext arguments from Python
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
        };

        // 4. Capture and Resample Mic Audio
        const source = window.mercuryAudioContext.createMediaStreamSource(window.mercuryMicStream);
        const processor = window.mercuryAudioContext.createScriptProcessor(4096, 1, 1);
        
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
                
                // CRITICAL: Convert Float32 to PCM 16-bit
                const pcm16 = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    pcm16[i] = Math.max(-1, Math.min(1, inputData[i])) * 32767;
                }
                window.mercuryWebSocket.send(pcm16.buffer);
            }
        };

        // 5. Receive Voice or Commands from Server
        window.mercuryWebSocket.onmessage = async (event) => {
            
            // CHECK 1: Did the server send a TEXT command to close the mic?
            if (typeof event.data === "string") {
                if (event.data === "CLOSE_MIC") {
                    console.log("🛑 Gemini finished speaking. Auto-closing microphone...");
                    
                    // 🚀 THE FIX: Use innerText for robust button selection in React/Reflex
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const stopBtn = buttons.find(b => b.innerText.includes("Stop Interrupt"));
                    
                    if (stopBtn) {
                        console.log("👉 Simulating click on Stop Interrupt button...");
                        stopBtn.click();
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