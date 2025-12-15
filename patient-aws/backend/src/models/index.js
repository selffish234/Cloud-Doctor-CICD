/**
 * Models Index - 모든 모델을 한 곳에서 관리
 */

const { sequelize, testConnection, initDatabase } = require('../config/database');
const User = require('./User');
const Post = require('./Post');

module.exports = {
  sequelize,
  testConnection,
  initDatabase,
  User,
  Post
};
