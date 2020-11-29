const path = require('path');
// const cpy = require('cpy');

module.exports = {
    makers: [
        {
            name: '@electron-forge/maker-squirrel',
            config: {
                name: 'electron_forge_webpack',
            },
        },
        {
            name: '@electron-forge/maker-zip',
            platforms: ['darwin'],
        },
        {
            name: '@electron-forge/maker-deb',
            config: {},
        },
    ],
    hooks: {
        generateAssets:
            async () => {

                // generate assets by platform type
                console.log(process.platform);

                console.log('On hook packageAfterExtract');
                var ncp = require('ncp').ncp;

                const del = require('del');
                ncp.limit = 16;

                await del(['./static/deplatformer-linux']);

                ncp("../dist/deplatformer-linux", "./static/deplatformer-linux/", function (err) {
                    if (err) {
                        return console.error(err);
                    }
                    console.log('done!');
                });
                console.log('Files copied!');
            },
        // packageAfterExtract:
    },
    // plugins: [
    //     [
    //         // '@electron-forge/plugin-webpack',
    //         // {
    //         //     mainConfig: './webpack.main.config.js',
    //         //     renderer: {
    //         //         config: './webpack.renderer.config.js',
    //         //         entryPoints: [
    //         //             {
    //         //                 html: './src/index.html',
    //         //                 js: './src/renderer.js',
    //         //                 name: 'main_window',
    //         //             },
    //         //         ],
    //         //     },
    //         // },
    //     ],
    // ],
};