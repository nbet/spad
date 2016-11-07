{{'{%'}} set {{project_name}} = salt['pillar.get']('salt_parameters') {{'%}'}}

{{service_name}}_install_path:
  file.directory:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - mode: 755
    - makedirs: true

{{service_name}}_pkg_available_path:
  file.directory:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_available
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - mode: 755
    - makedirs: true
    - require:
      - file: {{service_name}}_install_path

{{service_name}}_pkg_installed_path:
  file.directory:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_installed
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - mode: 755
    - makedirs: true
    - require:
      - file: {{service_name}}_install_path

{{service_name}}_pkg:
  file.managed:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_available/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}.tar.gz
    - source:  http://{{'{{'}}{{project_name}}.repo_addr{{'}}'}}/{{project_name|upper}}/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}.tar.gz
    - source_hash: http://{{'{{'}}{{project_name}}.repo_addr{{'}}'}}/{{project_name|upper}}/sha512/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}.sha512
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}

{{service_name}}_pkg_link:
  file.symlink:
    - name: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_installed/{{service_name}}
    - target: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_available/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}.tar.gz
    - force: True
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - require:
      - file: {{service_name}}_pkg

{{service_name}}_pkg_install:
  cmd.wait:
    - name: tar zxvf {{service_name}} -C {{'{{'}}{{project_name}}.install_path{{'}}'}}
    - cwd: {{'{{'}}{{project_name}}.install_path{{'}}'}}/pkg_installed
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - watch:
      - file: {{service_name}}_pkg_link

{{'{{'}}{{project_name}}.install_path{{'}}'}}/{{service_name}}:
  file.recurse:
    - source: salt://files/config/{{service_name}}-{{'{{'}}{{project_name}}.{{service_name}}{{'}}'}}-config
    - template: jinja
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - file_mode:  544
    - defaults:    
    {{'{%'}} for key, value in {{project_name}}.iteritems() {{'%}'}}
{%- raw %}
      {{key}}: {{value}}
    {% endfor %}
{%- endraw %}


{{project_name}}_supervisord_conf:
  file.managed:
    - name: {{'{{'}}{{project_name}}.software_install_path{{'}}'}}/supervisor/supervisord.conf
    - source: {{'{{'}}{{project_name}}.install_path{{'}}'}}/service_project/supervisor/supervisord.conf
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}

{{project_name}}_supervisorctl_reread:
  cmd.wait:
     -name: supervisorctl reread -c {{'{{'}}{{project_name}}.software_install_path{{'}}'}}/supervisor/supervisord.conf
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - watch:
      - file: {{project_name}}_supervisord_conf


{{project_name}}_supervisorctl_update:
  cmd.wait:
    - name: supervisorctl update -c {{'{{'}}{{project_name}}.software_install_path{{'}}'}}/supervisor/supervisord.conf
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - group: {{'{{'}}{{project_name}}.group{{'}}'}}
    - require:
      - cmd: {{project_name}}_supervisorctl_reread

{{'{%'}} for name in {{project_name}}.start_service {{'%}'}}
{{project_name}}_start_{{'{{'}}loop.index{{'}}'}}:
  supervisord.running:
    - name: {{'{{'}}name{{'}}'}}
    - update: true
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - conf_file: {{'{{'}}{{project_name}}.software_install_path{{'}}'}}/supervisor/supervisord.conf
    - bin_env: {{'{{'}}{{project_name}}.software_install_path{{'}}'}}/anaconda
    - watch:
      - file: {{project_name}}_supervisord_conf
{{'{%'}} endfor {{'%}'}}


{{'{%'}} for name in {{project_name}}.stop_service {{'%}'}}
{{project_name}}_stop_{{'{{'}}loop.index{{'}}'}}:
  supervisord.dead:
    - name: {{'{{'}}name{{'}}'}}
    - user: {{'{{'}}{{project_name}}.user{{'}}'}}
    - conf_file: {{'{{'}}{{project_name}}.software_install_path{{'}}'}}/supervisor/supervisord.conf
    - bin_env: {{'{{'}}{{project_name}}.software_install_path{{'}}'}}/anaconda
    - watch:
      - file: {{project_name}}_supervisord_conf
{{'{%'}} endfor {{'%}'}}




