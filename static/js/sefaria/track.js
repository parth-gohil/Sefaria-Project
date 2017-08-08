var ga = require('./sefariaGa');

class Track {
    // Helper functions for event tracking (with Google Analytics and Mixpanel)
    static event(category, action, label, value, options) {
        console.log('tracking called');
        console.log(value);
        console.log(options);
        // https://developers.google.com/analytics/devguides/collection/analyticsjs/command-queue-reference#send

        if (value && value.hitCallback) {
            console.log('hitcallback exists y\'all');
        }

        ga('send', 'event', category, action, label, value, options);
        //console.log('send', 'event', category, action, label, value, options);
        if (ga._mock && value && value.hitCallback) {
          // When Google Analytics isn't being used, trigger hitCallback immediately.
          value.hitCallback();
          // Unsure why we have param mismatch... what we call value here is treated as options.
          // A previous attempt to insert `null` for value to put `options` in the right place broke tracking.
        }
    }
    static pageview(url) {
        ga('set', 'page', url);
        ga('send', 'pageview');
    }
    static setPrimaryCategory(category_name) {
        ga('set', 'contentGroup1', category_name);
    }
    static setSecondaryCategory(category_name) {
        ga('set', 'contentGroup2', category_name);
    }
    static setContentLanguage(language) {
        ga('set', 'contentGroup5', language);
    }
    static setNumberOfPanels(val) {
        ga('set', 'dimension1', val);
    }
    static setBookName(val) {
        ga('set', 'dimension2', val);
        ga('set', 'contentGroup3', val);
    }
    static setRef(val) {
        ga('set', 'dimension3', val);
    }
    static setVersionTitle(val) {
        ga('set', 'dimension4', val);
    }
    static setPageType(val) {
        ga('set', 'dimension5', val);
    }
    static setSidebars(val) {
        ga('set', 'dimension6', val);
    }
    static setUserLoggedIn(bool) {
        ga('set', 'dimension7', bool? "Logged In": "Logged Out");
    }
    static setUserPartnerGroup(val) {
        ga('set', 'dimension8', val);
    }
    static setUserPartnerRole(val) {
        ga('set', 'dimension9', val);
    }
    static setUserID(val) {
        var sval = String(val);
        ga('set', 'userId', sval);
        ga('set', 'dimension10', sval);
    }
    static setUserData(loggedIn, partner_group, partner_role, analytics_uid) {
        this.setUserLoggedIn(loggedIn);
        if (partner_group) this.setUserPartnerGroup(partner_group);
        if (partner_role) this.setUserPartnerRole(partner_role);
        if (analytics_uid) this.setUserID(analytics_uid);
    }
    static sheets(action, label) {
        this.event("Sheets", action, label);
    }
    static exploreUrl(url) {
        this.event("Explorer", "Open", url);
        this.pageview(url);
    }
    static exploreBook(book) {
        this.event("Explorer", "Book", book);
    }
    static exploreBrush(book) {
        this.event("Explorer", "Brush", book);
    }
    static setInterfaceLanguage(origin, language){
        // Tracks a user setting their interface langauge, which can be done either account settings or footer
        this.event("Settings", origin, language);
    }
}

module.exports = Track;
