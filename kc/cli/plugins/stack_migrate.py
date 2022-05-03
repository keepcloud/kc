from cement.core.controller import CementBaseController, expose

from kc.cli.plugins.stack_pref import post_pref, pre_pref
from kc.core.aptget import KCAptGet
from kc.core.fileutils import KCFileUtils
from kc.core.logging import Log
from kc.core.mysql import KCMysql
from kc.core.shellexec import KCShellExec
from kc.core.variables import KCVar
from kc.core.apt_repo import KCRepo


class KCStackMigrateController(CementBaseController):
    class Meta:
        label = 'migrate'
        stacked_on = 'stack'
        stacked_type = 'nested'
        description = ('Migrate stack safely')
        arguments = [
            (['--mariadb'],
                dict(help="Migrate/Upgrade database to MariaDB",
                     action='store_true')),
            (['--force'],
                dict(help="Force Packages upgrade without any prompt",
                     action='store_true')),
            (['--ci'],
                dict(help="Argument used for testing, "
                     "do not use it on your server",
                     action='store_true')),
        ]

    @expose(hide=True)
    def migrate_mariadb(self, ci=False):
        # Backup all database
        KCMysql.backupAll(self, fulldump=True)

        # Remove previous MariaDB repository
        kc_mysql_old_repo = (
            "deb [arch=amd64,ppc64el] "
            "http://mariadb.mirrors.ovh.net/MariaDB/repo/"
            "10.3/{distro} {codename} main"
            .format(distro=KCVar.kc_distro,
                    codename=KCVar.kc_platform_codename))
        if KCFileUtils.grepcheck(
                self, '/etc/apt/sources.list.d/kc-repo.list',
                kc_mysql_old_repo):
            KCRepo.remove(self, repo_url=kc_mysql_old_repo)
        # Add MariaDB repo
        pre_pref(self, KCVar.kc_mysql)

        # Install MariaDB

        Log.wait(self, "Updating apt-cache          ")
        KCAptGet.update(self)
        Log.valide(self, "Updating apt-cache          ")
        Log.wait(self, "Upgrading MariaDB          ")
        KCAptGet.remove(self, ["mariadb-server"])
        KCAptGet.auto_remove(self)
        KCAptGet.install(self, KCVar.kc_mysql)
        if not ci:
            KCAptGet.dist_upgrade(self)
        KCAptGet.auto_remove(self)
        Log.valide(self, "Upgrading MariaDB          ")
        KCFileUtils.mvfile(
            self, '/etc/mysql/my.cnf', '/etc/mysql/my.cnf.old')
        KCFileUtils.create_symlink(
            self, ['/etc/mysql/mariadb.cnf', '/etc/mysql/my.cnf'])
        KCShellExec.cmd_exec(self, 'systemctl daemon-reload')
        KCShellExec.cmd_exec(self, 'systemctl enable mariadb')
        post_pref(self, KCVar.kc_mysql, [])

    @expose(hide=True)
    def default(self):
        pargs = self.app.pargs
        if ((not pargs.mariadb)):
            self.app.args.print_help()
        if pargs.mariadb:
            if KCVar.kc_distro == 'raspbian':
                Log.error(self, "MariaDB upgrade is not available on Raspbian")
            if KCVar.kc_mysql_host != "localhost":
                Log.error(
                    self, "Remote MySQL server in use, skipping local install")

            if (KCShellExec.cmd_exec(self, "mysqladmin ping")):

                Log.info(self, "If your database size is big, "
                         "migration may take some time.")
                Log.info(self, "During migration non nginx-cached parts of "
                         "your site may remain down")
                if not pargs.force:
                    start_upgrade = input("Do you want to continue:[y/N]")
                    if start_upgrade != "Y" and start_upgrade != "y":
                        Log.error(self, "Not starting package update")
                if not pargs.ci:
                    self.migrate_mariadb()
                else:
                    self.migrate_mariadb(ci=True)
            else:
                Log.error(self, "Your current MySQL is not alive or "
                          "you allready installed MariaDB")
