export const initDB = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TOBU_WorkspaceDB', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('handles')) {
        db.createObjectStore('handles', { keyPath: 'path' });
      }
    };
  });
};

export const storeHandle = async (path, handle) => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('handles', 'readwrite');
    const store = tx.objectStore('handles');
    const request = store.put({ path, handle });

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

export const getHandle = async (path) => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('handles', 'readonly');
    const store = tx.objectStore('handles');
    const request = store.get(path);

    request.onsuccess = () => resolve(request.result?.handle);
    request.onerror = () => reject(request.error);
  });
};

export const getAllHandles = async () => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('handles', 'readonly');
    const store = tx.objectStore('handles');
    const request = store.getAll();

    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
};

export const deleteHandle = async (path) => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('handles', 'readwrite');
    const store = tx.objectStore('handles');
    const request = store.delete(path);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

export const verifyPermission = async (fileHandle, readWrite = false) => {
  const options = { mode: readWrite ? 'readwrite' : 'read' };
  
  if ((await fileHandle.queryPermission(options)) === 'granted') {
    return true;
  }
  
  if ((await fileHandle.requestPermission(options)) === 'granted') {
    return true;
  }
  
  return false;
};
