const loadedScripts = new Map();

export const loadScriptOnce = (src) => {
	if (loadedScripts.has(src)) return loadedScripts.get(src);
	const promise = new Promise((resolve, reject) => {
		const script = document.createElement('script');
		script.src = src;
		script.async = true;
		script.onload = () => resolve();
		script.onerror = (err) => reject(err);
		document.head.appendChild(script);
	});
	loadedScripts.set(src, promise);
	return promise;
};
