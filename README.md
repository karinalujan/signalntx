# S/GNAL single-page prototype

A dependency-free replacement prototype consolidating the live Home, Directory, Community + Events, About, and Contact pages. Run it locally with `python3 -m http.server 8000` and visit `http://localhost:8000`.

The directory is deliberately marked under construction. The original directory's nine entries are retained as links in the expandable resources section. The calendar contains the original site's August–September 2026 exhibition as an archived event. Edit `events.js` to add reviewed events, using inclusive `YYYY-MM-DD` start and end dates; supply real event URLs and details rather than Instagram post dates. The calendar opens to the current month and can be navigated to past months.

## Before publishing

- The contact form opens an email draft to `hello@karinalujan.design` in the visitor's email application; it does not send messages on its own. A direct email link is provided when JavaScript is unavailable. The original Webflow form appears to have its message field incorrectly configured as an email field.
- Confirm the existing listings and event details are still accurate. The original Meow Wolf link pointed to Make Space; this prototype uses the Meow Wolf URL shown in the original link text.
- Set up hosting, redirects for the original page URLs, and any desired domain/DNS changes separately. Nothing here publishes to Webflow or changes the live site.

## Instagram integration

The local review tool uses Meta's official Instagram API with Instagram Login. It is not connected until you authorize it:

1. Create a Business-type Meta app and add the Instagram product using Meta's [app setup instructions](https://developers.facebook.com/documentation/instagram-platform/create-an-instagram-app). Add and authorize the professional account **@lujan.creative**, with the `instagram_business_basic` permission. Standard Access is intended for accounts you own or manage and add to your app.
2. In the app dashboard, open **Instagram > API setup with Instagram business login**, generate a token for the account, and keep it private. See Meta's [getting-started guide](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/get-started) for current steps. Do not paste the token into chat or put it in a website file.
3. Run `python3 instagram_review.py` on your computer. Paste the token at the hidden prompt. The tool checks the username, lists the first page of the account's posts, and asks you to open each Instagram link and decide whether to add an event. It does not read captions; consult the original post for details. The post's publication date is **not** the event date.
4. Enter the verified event information, including its local dates and any event time and time zone. Each approved event is saved to `instagram-events.js`; reload the local site to see it. Publish that file with the site when you are ready. To change or remove an imported event, edit the corresponding entry in that file. Keep its JSON structure and `sourceId` intact.

The tool only reads posts from the authorized account, not arbitrary local Instagram pages. It does not automatically infer events or publish them. Only the first page of posts is reviewed; it warns if more are available. Meta says dashboard-generated tokens are typically valid for 60 days; regenerate or refresh them before expiry following its documentation. The tool doesn't save or refresh tokens. It cannot be tested against the live account until the app and token are configured.
