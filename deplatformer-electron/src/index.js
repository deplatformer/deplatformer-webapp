const { app, BrowserWindow } = require('electron');
const path = require('path');
const {spawn} = require('child_process');

let pids = []


// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) { // eslint-disable-line global-require
  app.quit();
}

const createWindow = async () => {
  // Create the browser window.


  let dataToSend;
  // spawn new child process to call the python script
  let python
  try {
    if (process.platform === 'linux') {
      python = await spawn('../dist/deplatformer-linux/deplatformer'); //, ['script1.py']);
      pids = pids.concat( [python] );
    } else {
      throw Error();
    }
  } catch (err) {
    console.log(err);
    app.quit();
  } finally {

  }

  // collect data from script
  python.stdout.on('data', function (data) {
    console.log('Pipe data from python script ...');
    dataToSend = data.toString();
    // console.log(dataToSend);

    const mainWindow = new BrowserWindow({
      width: 1920,
      height: 1440,
    });
    mainWindow.loadURL("http://localhost:5000/");

    if (dataToSend.includes("Serving Flask app")){
      // and load the index.html of the app.;
    }
  });
  // in close event we are sure that stream from child process is closed
  python.on('close', (code) => {
    console.log(`child process close all stdio with code ${code}`);
    // send data to browser
    // res.send(dataToSend)
    console.log(dataToSend);
  });


//  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Open the DevTools.
//  mainWindow.webContents.openDevTools();
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow);

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', async () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
  pids.forEach(async function(proc) {
    // A simple pid lookup
    // ps.kill( pid, function( err ) {
    //   if (err) {
    //     throw new Error( err );
    //   }
    //   else {
    //     console.log( 'Process %s has been killed!', pid );
    //   }
    // });
    console.log("KILLING WITH SIGINT");
    console.log(proc.pid);
    await proc.kill("SIGKILL")
    console.log("KILLED");
  });
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// App close handler
app.on('before-quit', function() {
});
// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.
