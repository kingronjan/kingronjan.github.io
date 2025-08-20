FROM docker.m.daocloud.io/ruby:3.3

RUN gem sources --add https://mirrors.tuna.tsinghua.edu.cn/rubygems/ --remove https://rubygems.org/
RUN bundle config mirror.https://rubygems.org https://mirrors.tuna.tsinghua.edu.cn/rubygems
RUN gem install bundler jekyll

WORKDIR /app

RUN bundle install

CMD ["bundle", "exec", "jekyll", "serve", "-H", "0.0.0.0"]

