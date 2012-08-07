// Set the require.js configuration for your application.
require.config({

  // Initialize the application with the main application file.
  deps: ["main"],

  paths: {
    // JavaScript folders.
    libs: "../assets/js/libs",
    plugins: "../assets/js/plugins",
    modules: "modules",

    // Libraries.
    jquery: "../assets/js/libs/jquery",
    lodash: "../assets/js/libs/lodash",
    backbone: "../assets/js/libs/backbone",
    // Couch related Libraries.
    json2: "../assets/js/libs/json2",
    underscore: "../assets/js/libs/underscore",
    backbonecouch: "../assets/js/libs/backbone-couch",
    jquerycouch: "../assets/js/libs/jquery-couch"
  },

  shim: {
    // Backbone library depends on lodash and jQuery.
    backbone: {
      deps: ["lodash", "jquery"],
      exports: "Backbone"
    },
    // not sure if this should export anything...
    jquerycouch: ["jquery", "json2"],
    backbonecouch: {
      deps: ["backbone", "jquerycouch", "underscore"],
      // not sure what exports should be...
      exports: "Backbone.Couch"
    },

    // Backbone.LayoutManager depends on Backbone.
    "plugins/backbone.layoutmanager": ["backbone"]
  }
});
