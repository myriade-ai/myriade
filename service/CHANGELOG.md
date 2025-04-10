# CHANGELOG


## v0.8.6 (2025-04-10)

### Bug Fixes

- Myr-244
  ([`93b0603`](https://github.com/myriade-intelligence/ada/commit/93b0603811831028aaa09e8b24f8e83faebb8f3a))

- Update snapshot
  ([`06415e7`](https://github.com/myriade-intelligence/ada/commit/06415e7e7b6eb47cc7b07f2b2b271a94493fbd08))


## v0.8.5 (2025-04-09)

### Bug Fixes

- Reset stop flag if the user started a new query
  ([`8ea6f60`](https://github.com/myriade-intelligence/ada/commit/8ea6f602a2e4f551ee8a22e788cd4593f8b6b9cf))

MYR-242


## v0.8.4 (2025-04-09)

### Bug Fixes

- Refresh page flickering
  ([`d05f161`](https://github.com/myriade-intelligence/ada/commit/d05f16192c6edbde5a77ceafe87734944b7b633c))

MYR-246

### Build System

- Add proxy in docker compose
  ([`d5b71d9`](https://github.com/myriade-intelligence/ada/commit/d5b71d95ae45770805580340bbbdcdf1cd1ec0a2))

- Update deploy script
  ([`e9f7ba9`](https://github.com/myriade-intelligence/ada/commit/e9f7ba9855b64054401693b47ee7ce4f2ddee3ab))


## v0.8.3 (2025-04-08)

### Bug Fixes

- Add missing nest-asyncio dep
  ([`fa8e36a`](https://github.com/myriade-intelligence/ada/commit/fa8e36a2e0d0e6587901028c9f0a11e4489d6960))

- Upgrade dep + fix async work
  ([`670ac2d`](https://github.com/myriade-intelligence/ada/commit/670ac2d2d3207e0077d047872d42c585aad08392))


## v0.8.2 (2025-04-04)

### Bug Fixes

- Correctly follow the "privacy mode" parameters
  ([`c1db1c7`](https://github.com/myriade-intelligence/ada/commit/c1db1c733d00eb23f9eb4efdfbd6a6bad00d331c))

MYR-230

### Chores

- Update website
  ([`f1f90b6`](https://github.com/myriade-intelligence/ada/commit/f1f90b6f6b5875e668e5715ebf6ef28a8ec8c9e7))


## v0.8.1 (2025-03-31)

### Performance Improvements

- Rework imports
  ([`51d9fc9`](https://github.com/myriade-intelligence/ada/commit/51d9fc9431e9116e827de51ea853ac0aac267670))


## v0.8.0 (2025-03-31)

### Build System

- Add script to update servers
  ([`20a2fa9`](https://github.com/myriade-intelligence/ada/commit/20a2fa95c299597d5faa84a98fed2727de4ccffa))

PRO-220

### Features

- Add homepage
  ([`e941027`](https://github.com/myriade-intelligence/ada/commit/e9410275c19e69129aa051295e36f090e0095db2))


## v0.7.1 (2025-03-30)

### Bug Fixes

- Switch to long pooling
  ([`f67f9b3`](https://github.com/myriade-intelligence/ada/commit/f67f9b3a2019edc4761f743f527f897e5d24861a))


## v0.7.0 (2025-03-29)

### Bug Fixes

- Display of connection error
  ([`5ce9b8f`](https://github.com/myriade-intelligence/ada/commit/5ce9b8f6cf222080e6ed4d356616327db3b42eda))

- Horizontal display on mobile
  ([`21f7939`](https://github.com/myriade-intelligence/ada/commit/21f793948535e8c5aff808d5ef9d2e348236ad3c))

- Keep context in localstorage, update vue,vite,vue-router
  ([`3c3d08c`](https://github.com/myriade-intelligence/ada/commit/3c3d08cd3c7d45f9bcfcbfea0051c10216145fef))

### Build System

- Add gunicorn
  ([`31946e7`](https://github.com/myriade-intelligence/ada/commit/31946e7fee85e3eea1b861b737425fd0c518d295))

### Chores

- Add support for local mode
  ([`9e3d854`](https://github.com/myriade-intelligence/ada/commit/9e3d8547d81c041d774f554c34366af3490282d3))

- Remove sentry for local
  ([`ed7c92b`](https://github.com/myriade-intelligence/ada/commit/ed7c92b6a501d7f69ab855d0ed8ad073f3258c08))

PRO-219

### Features

- Improve ux for mobile
  ([`f55b873`](https://github.com/myriade-intelligence/ada/commit/f55b87343b01c658c4389581beeabccc126b3d94))


## v0.6.13 (2025-03-28)

### Bug Fixes

- Websocket connection
  ([`a05daef`](https://github.com/myriade-intelligence/ada/commit/a05daef7c2a7ab4668d4af5382cb82f512b790e5))

by forcing reconnect...

### Chores

- Improve sent message dynamic
  ([`4998ef0`](https://github.com/myriade-intelligence/ada/commit/4998ef046aead4577359f2d89da1bbc6498dde95))


## v0.6.12 (2025-03-27)

### Bug Fixes

- Add organization in log
  ([`40677ca`](https://github.com/myriade-intelligence/ada/commit/40677ca94af1397639cf1f7bdbe7ab96a4bedcbb))


## v0.6.11 (2025-03-27)

### Bug Fixes

- Migration bug
  ([`eea8058`](https://github.com/myriade-intelligence/ada/commit/eea8058b4077adf453e50f7543ca841576692d75))


## v0.6.10 (2025-03-27)

### Bug Fixes

- Re-add logout on 401
  ([`52248b5`](https://github.com/myriade-intelligence/ada/commit/52248b52a4385aebbb9fa554998632acacf40c36))


## v0.6.9 (2025-03-27)

### Bug Fixes

- Debug auth
  ([`f919bcc`](https://github.com/myriade-intelligence/ada/commit/f919bcc8819860836118b7941880e3e00cb202bc))


## v0.6.8 (2025-03-27)

### Bug Fixes

- Try to debug login
  ([`517cd68`](https://github.com/myriade-intelligence/ada/commit/517cd68810af12522f8f0b6ae10fb2e256959603))


## v0.6.7 (2025-03-27)

### Bug Fixes

- Redirect correctly to /login
  ([`84687f1`](https://github.com/myriade-intelligence/ada/commit/84687f183c10dfd833e17bb2ba11cffd6430fc3a))


## v0.6.6 (2025-03-27)

### Bug Fixes

- Logout when 401
  ([`28985e0`](https://github.com/myriade-intelligence/ada/commit/28985e060125addceaec621f897a07fd2b557a9f))


## v0.6.5 (2025-03-27)

### Bug Fixes

- Improve logout/login
  ([`21d4c89`](https://github.com/myriade-intelligence/ada/commit/21d4c89d0c6c2b76040c403bb2863f4a6236a7f1))

Also remove Crisp


## v0.6.4 (2025-03-26)

### Bug Fixes

- Remove user outside org
  ([`ce1f532`](https://github.com/myriade-intelligence/ada/commit/ce1f5329c810b02d3d5399112ccdce366b1ba555))


## v0.6.3 (2025-03-26)

### Bug Fixes

- Add organization in session refresh
  ([`e770c54`](https://github.com/myriade-intelligence/ada/commit/e770c548819d6d2a92b61624b04a391bcf68b32e))


## v0.6.2 (2025-03-26)

### Bug Fixes

- Verify that the user belong to the organisation
  ([`ddbbdef`](https://github.com/myriade-intelligence/ada/commit/ddbbdef980bc716d4f1542f3fa260986bca44a8b))

### Chores

- Clean setup
  ([`44ee6ca`](https://github.com/myriade-intelligence/ada/commit/44ee6caaaa5ea85732bbc972015dd8d299e72c95))

- Upgrade socket packages
  ([`bed53e3`](https://github.com/myriade-intelligence/ada/commit/bed53e3d9cfaa704ecb01d3197922ed45fc930d8))


## v0.6.1 (2025-03-26)

### Bug Fixes

- Socket bugs PRO-190
  ([`607a62e`](https://github.com/myriade-intelligence/ada/commit/607a62e7e6a4a217a7596d756608f9bcb1142e9e))

### Chores

- Improve socket
  ([`9e3aabc`](https://github.com/myriade-intelligence/ada/commit/9e3aabc009c7904995b284fe66e502efa8d6c51a))

- Move components & move to abs imports
  ([`ac2abce`](https://github.com/myriade-intelligence/ada/commit/ac2abcea6870d11e85bd37be0e69524f56233293))

- Switch to 100 composition api
  ([`b1a6497`](https://github.com/myriade-intelligence/ada/commit/b1a649718021006b3ee80b4a624ad2f37a0433b7))


## v0.6.0 (2025-03-20)

### Chores

- Add 404 page
  ([`053ce7b`](https://github.com/myriade-intelligence/ada/commit/053ce7b8e84115d11766776eb7ebd4a8c5fef164))

- Add sentry env
  ([`2499bfc`](https://github.com/myriade-intelligence/ada/commit/2499bfccb9a7607d62944cea24f247e623bbaa82))

- Avoid release workflow on failed tests
  ([`fe0e257`](https://github.com/myriade-intelligence/ada/commit/fe0e257cf8b30ec4d5e02d222694611d6809ca5b))

- Fix PRO-180
  ([`97b33fd`](https://github.com/myriade-intelligence/ada/commit/97b33fda3b8dce46095780393ba4ac4c12cdaf82))

- Fix test
  ([`90d7680`](https://github.com/myriade-intelligence/ada/commit/90d768087d6d78d97389a8af1466311cda84c886))

- Have AI suggestion in user language PRO-11
  ([`66bdb0f`](https://github.com/myriade-intelligence/ada/commit/66bdb0fd3dc69cc2efe1f9a85afb22611d6431e2))

- Improve code so release don't trigger tests
  ([`d0838d5`](https://github.com/myriade-intelligence/ada/commit/d0838d5756e9db0c69dd41b1fede944d343a5049))

- Reload page on version update
  ([`bbabc56`](https://github.com/myriade-intelligence/ada/commit/bbabc563b42f22f34455cdbac6b6d2e784fd55cf))

### Features

- Edit message
  ([`39c8423`](https://github.com/myriade-intelligence/ada/commit/39c84237b9bf234d33bf10737fe36b72e75d2c07))

* Add ability to edit and re-run user message


## v0.5.6 (2025-03-19)

### Bug Fixes

- Improve socket and loading icon
  ([`7e8fe67`](https://github.com/myriade-intelligence/ada/commit/7e8fe67373be59738ccfc689f4f8ab225906c880))

### Chores

- Add .terminal.json
  ([`00c6238`](https://github.com/myriade-intelligence/ada/commit/00c62383a54841f0da6ad2aa6a4f08055778e571))

- Redirect / to /chat/new
  ([`a2685fd`](https://github.com/myriade-intelligence/ada/commit/a2685fd41a39be2ea04e88c2a99d6864d6f401e7))

- Remove bad code
  ([`a8b4b5e`](https://github.com/myriade-intelligence/ada/commit/a8b4b5e4ad1289dda5a43e331c5d1c36714e168b))


## v0.5.5 (2025-03-19)

### Bug Fixes

- Datetime json support PRO-174
  ([`7bb985c`](https://github.com/myriade-intelligence/ada/commit/7bb985c057f0960c1bc57f56633a601773660881))


## v0.5.4 (2025-03-19)

### Bug Fixes

- Add missing pyyaml
  ([`d1262b5`](https://github.com/myriade-intelligence/ada/commit/d1262b527a8e025ccc11559eb3379b75a6be4e87))


## v0.5.3 (2025-03-19)

### Bug Fixes

- Add missing sentry
  ([`8ca8012`](https://github.com/myriade-intelligence/ada/commit/8ca8012ec69323d425da79ae26a2fa0d9508bda6))


## v0.5.2 (2025-03-19)

### Bug Fixes

- Clean code
  ([`85f63d3`](https://github.com/myriade-intelligence/ada/commit/85f63d33190feca3fd4f4810d841689c648118a5))


## v0.5.1 (2025-03-18)

### Bug Fixes

- Remove visualisationParams
  ([`3fe83bc`](https://github.com/myriade-intelligence/ada/commit/3fe83bcf38576e4753db2223acff0c7e94d5b271))


## v0.5.0 (2025-03-17)

### Chores

- Add crisp
  ([`d7f07a6`](https://github.com/myriade-intelligence/ada/commit/d7f07a6f1a04cb9580676173563700edbbb320c0))

- Add front linter
  ([`a475a1d`](https://github.com/myriade-intelligence/ada/commit/a475a1ddf0022e9c9d1c28c701bdd6e26c48de8d))

- Add strict
  ([`f6e1888`](https://github.com/myriade-intelligence/ada/commit/f6e1888fd16f51e25eda25b92cfa60326a06dea7))

- Fix test workflow
  ([`238f298`](https://github.com/myriade-intelligence/ada/commit/238f29831c0550dcda1b3968ee6bc5a03d953960))

- Remove
  ([`96c7384`](https://github.com/myriade-intelligence/ada/commit/96c7384ded425c879aafea81e485f82b2e061379))

PRO-102

- Remove dead code
  ([`6325879`](https://github.com/myriade-intelligence/ada/commit/63258791df382a6943d1608dc0e40cbafabc6b56))

- Remove unused column embedding
  ([`a7041e7`](https://github.com/myriade-intelligence/ada/commit/a7041e7d94bf17b23eb98719adf20958f1352582))

- Remove unused dep
  ([`0c64706`](https://github.com/myriade-intelligence/ada/commit/0c647060c68bffec4dad1bc09e2076da30adf195))

- Remove unused dep
  ([`650c0e0`](https://github.com/myriade-intelligence/ada/commit/650c0e012f5763489d84386dab07522098e41471))

- Remove visualisation params
  ([`1266517`](https://github.com/myriade-intelligence/ada/commit/1266517b0f15f612ef2524b848326b160efddef4))

PRO-103

- Update test workflow
  ([`c3f3ccf`](https://github.com/myriade-intelligence/ada/commit/c3f3ccfa1849fda33137e6b97f44a2a0fec9f541))

### Features

- Add sentry
  ([`8fd69a6`](https://github.com/myriade-intelligence/ada/commit/8fd69a6feb4ef63212b893eb27741e77fb96a4ec))


## v0.4.6 (2025-03-15)

### Bug Fixes

- Always consider chart as answer
  ([`f7030a8`](https://github.com/myriade-intelligence/ada/commit/f7030a8aa96234bcbe4254e724da6bc3320deb62))

### Chores

- Fix pyproject release
  ([`216b730`](https://github.com/myriade-intelligence/ada/commit/216b7306c3453c8dd309d7e23ca3d8a0e8863cdb))


## v0.4.5 (2025-03-15)

### Bug Fixes

- Loading status in different conversions
  ([`4eefa0e`](https://github.com/myriade-intelligence/ada/commit/4eefa0e1d691aeb742823a064d844b1a1d606d24))


## v0.4.4 (2025-03-15)

### Bug Fixes

- New page redirection PRO-116
  ([`a9cab26`](https://github.com/myriade-intelligence/ada/commit/a9cab26b5eb90c60d3b582e9b6786b54caa50457))

### Chores

- Add version ([#29](https://github.com/myriade-intelligence/ada/pull/29),
  [`572c4a4`](https://github.com/myriade-intelligence/ada/commit/572c4a40ea8b03faed2c03bd3b96b1ffe1f826e1))


## v0.4.3 (2025-03-09)

### Bug Fixes

- Bug delete conversation messages...
  ([`b13cb27`](https://github.com/myriade-intelligence/ada/commit/b13cb27937efa4790425f4fba00851cef5a3b127))

PRO-118


## v0.4.2 (2025-03-08)

### Bug Fixes

- **serialisation**: Decimal
  ([`bdc391b`](https://github.com/myriade-intelligence/ada/commit/bdc391b52c6d0dc990497cc138c237ed6c05bfcb))

PRO-112

- **session**: Try to catch exception and rollback
  ([`9edecac`](https://github.com/myriade-intelligence/ada/commit/9edecac7ca44701d6464389022c7bb560dd55867))

PRO-113


## v0.4.1 (2025-03-08)

### Bug Fixes

- **chart**: Render labels inside chart
  ([`680ea4a`](https://github.com/myriade-intelligence/ada/commit/680ea4a18a761cc3aab1472492b7cc229c95124b))


## v0.4.0 (2025-03-08)

### Features

- **chart**: Refacto / move from fusionchart to echarts
  ([#7](https://github.com/myriade-intelligence/ada/pull/7),
  [`4ddb122`](https://github.com/myriade-intelligence/ada/commit/4ddb122fb39e9e86f98c565324ea6cf60d3d8430))

* remove fusionchart, add echarts * remove playwright * remove retry * remove chart on page query
  (and components associated) * fix bugs on retry


## v0.3.12 (2025-03-05)

### Bug Fixes

- Test that use sqlite
  ([`b3e83ae`](https://github.com/myriade-intelligence/ada/commit/b3e83aed9bf574fd20e831890f5c9f36f3b93cf6))

### Chores

- Add offline mode
  ([`ad2976d`](https://github.com/myriade-intelligence/ada/commit/ad2976dd92bea8e6ee5f107e6083fd4919f1c885))

- Fixed
  ([`05d5bd9`](https://github.com/myriade-intelligence/ada/commit/05d5bd981ec35cf470edd91ca63f6e9afcedede5))


## v0.3.11 (2025-02-26)

### Bug Fixes

- Update plot widget functions
  ([`2af4bad`](https://github.com/myriade-intelligence/ada/commit/2af4bad73908e0073fd92c0c0769273a1b36a420))


## v0.3.10 (2025-02-26)

### Bug Fixes

- Function names
  ([`5021fa5`](https://github.com/myriade-intelligence/ada/commit/5021fa5ea43cb183a2a80061f13637b2136b1150))

### Chores

- Update autochat to v 0.9.2
  ([`0ccb5c3`](https://github.com/myriade-intelligence/ada/commit/0ccb5c3c9f16f09149c320d819c345b0e3a41bc4))


## v0.3.9 (2025-02-26)

### Bug Fixes

- Try to fix test run
  ([`e935d95`](https://github.com/myriade-intelligence/ada/commit/e935d9540e576faf95e32884d4b363fcdf0f6b37))

### Chores

- Add ip information for database timeout
  ([`8e206b7`](https://github.com/myriade-intelligence/ada/commit/8e206b782a5fad0d5a238aaf2ae1a35641b02f51))

- Add tests for functions and use autochat inspect schema for functions
  ([`dfbbf04`](https://github.com/myriade-intelligence/ada/commit/dfbbf04c9a84d0e1b5aa59a3704f8b92320a844b))

- Clean code
  ([`2a82b19`](https://github.com/myriade-intelligence/ada/commit/2a82b192e549d822a55ecc8e7490f055c4970ca1))

- Move tests
  ([`f459076`](https://github.com/myriade-intelligence/ada/commit/f45907601828b0827420d4b6a0e4444da7d8c9de))

- Update autochat to v 0.9.1
  ([`488b91e`](https://github.com/myriade-intelligence/ada/commit/488b91e211195a0c4ce8a84936bb959ac4ab19f2))


## v0.3.8 (2025-02-21)

### Bug Fixes

- Ruff
  ([`bdb0c40`](https://github.com/myriade-intelligence/ada/commit/bdb0c4072596921bde389de54ba0b15bb91cf912))


## v0.3.7 (2025-02-21)

### Bug Fixes

- Nginx setup and refresh token
  ([`9c5c158`](https://github.com/myriade-intelligence/ada/commit/9c5c158d6ec24dbd13a313b81179dccc409ae4cf))


## v0.3.6 (2025-02-21)

### Bug Fixes

- Add nginx proxy for auth
  ([`935910e`](https://github.com/myriade-intelligence/ada/commit/935910e9f6f955f8a6e3b81df25b0b20521c2df7))


## v0.3.5 (2025-02-21)

### Bug Fixes

- Add nginx proxy for auth
  ([`ea3f0f6`](https://github.com/myriade-intelligence/ada/commit/ea3f0f6fb98e886a82dfd9a0fae683382cd56d32))


## v0.3.4 (2025-02-21)

### Bug Fixes

- Add https scheme
  ([`feefac8`](https://github.com/myriade-intelligence/ada/commit/feefac810121e500b09cbecfdaee749fb54f8f58))


## v0.3.3 (2025-02-21)

### Bug Fixes

- Add start.sh
  ([`0f803d3`](https://github.com/myriade-intelligence/ada/commit/0f803d30dcd1c0f672be61959fb15499109f01d3))


## v0.3.2 (2025-02-21)

### Bug Fixes

- Dbt error
  ([`ba332a6`](https://github.com/myriade-intelligence/ada/commit/ba332a6def9047a6de6e2d32dad3c78311617668))


## v0.3.1 (2025-02-21)

### Bug Fixes

- Unathorized handling
  ([`dbde7e1`](https://github.com/myriade-intelligence/ada/commit/dbde7e1b3236aadad2e4cd5a2d24991097d6ed63))


## v0.3.0 (2025-02-21)

### Bug Fixes

- Fix docker scripts
  ([`5d1b380`](https://github.com/myriade-intelligence/ada/commit/5d1b380013a1b8cbdce2f00b06ebb8f42b18dac3))

### Features

- Improve scripts
  ([`a27e8eb`](https://github.com/myriade-intelligence/ada/commit/a27e8ebcd2730c4a70eac96ab8618affeb511242))


## v0.2.2 (2025-02-21)

### Bug Fixes

- Add user identification for socket
  ([`8273a5b`](https://github.com/myriade-intelligence/ada/commit/8273a5b10eed4eb2069a55c1ba9ed5176354918a))

### Chores

- Upgrade dependencies
  ([`d82225d`](https://github.com/myriade-intelligence/ada/commit/d82225df7f072b0f4535d8f0f3a6ccecae1adc68))


## v0.2.1 (2025-02-19)

### Bug Fixes

- **dependencies**: Add workos
  ([`aa922c3`](https://github.com/myriade-intelligence/ada/commit/aa922c3eb0e76b61b8645933f0e771981bf8d62d))


## v0.2.0 (2025-02-19)

### Features

- **readme**: Update
  ([`cb1f223`](https://github.com/myriade-intelligence/ada/commit/cb1f223ef5167fdc0afac345d0233f095831e833))


## v0.1.1 (2025-02-17)

### Bug Fixes

- Build
  ([`fad9940`](https://github.com/myriade-intelligence/ada/commit/fad9940c22817b03c63499872dfae2642e68fcd4))

### Chores

- Add build workflow
  ([`0c2945a`](https://github.com/myriade-intelligence/ada/commit/0c2945a94767fa2b984215d14306703aa923fd23))


## v0.1.0 (2025-02-17)

### Bug Fixes

- **postgresql**: Add port
  ([`f9f3f52`](https://github.com/myriade-intelligence/ada/commit/f9f3f527e9be290c50734f9a417358bf8df6e909))

### Chores

- Clean ruff
  ([`122b330`](https://github.com/myriade-intelligence/ada/commit/122b33008e55b04a7d6518c8314453bf146caad3))

- Ruff sort
  ([`e83ac6d`](https://github.com/myriade-intelligence/ada/commit/e83ac6d9031ad29d3650e57ad3b82d54c350eeba))

- **clean**: Add ruff
  ([`14eded4`](https://github.com/myriade-intelligence/ada/commit/14eded40a5643c0bf9acd6853f5beb648d9839a6))

- **clean**: Remove embedding, memory & tests
  ([`c8f35c7`](https://github.com/myriade-intelligence/ada/commit/c8f35c719c6b88cf135485e2426d97d80107405b))

### Features

- Allow connection to planetscale
  ([`2960cf8`](https://github.com/myriade-intelligence/ada/commit/2960cf874789fc2b69ed46fc8238f94811fe4ca1))

chore: make sure poetry.lock hash is correct
