const { app, BrowserWindow } = require('electron')

const createWindow = () => {
    const mainWindow = new BrowserWindow({
      width: 800,
      height: 600,
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
      }
    })
  
    mainWindow.loadFile('index.html')
    mainWindow.webContents.openDevTools(); // Open dev tools for mainWindow
  }

  app.whenReady().then(() => {
    createWindow()
  
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
  })


  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
  })